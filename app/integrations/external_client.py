import httpx
import asyncio
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import logging

import structlog
from app.core.retry_util import async_retry, ExternalServiceError, RateLimitError
from app.core.circuit_breaker import circuit_breaker, CircuitBreakerConfig
import time
import json
from urllib.parse import urljoin

logger = structlog.get_logger(__name__)

@dataclass
class ApiClientConfig:
    base_url: str
    timeout: float = 30.0
    max_retries: int = 3
    rate_limit_per_second: Optional[float] = None
    default_headers: Optional[Dict[str, str]] = None
    auth_token: Optional[str] = None
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None

class RateLimiter:
    def __init__(self, requests_per_second: float):
        self.requests_per_second = requests_per_second
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        async with self._lock:
            now = time.time()
            time_since_last = now - self.last_request_time
            min_interval = 1.0 / self.requests_per_second
            
            if time_since_last < min_interval:
                sleep_time = min_interval - time_since_last
                await asyncio.sleep(sleep_time)
            
            self.last_request_time = time.time()

class ExternalApiClient:
    def __init__(self, config: ApiClientConfig):
        self.config = config
        self.rate_limiter = None
        if config.rate_limit_per_second:
            self.rate_limiter = RateLimiter(config.rate_limit_per_second)
        
        headers = {
            "Content-Type": "application/json",
        }
        if config.default_headers:
            headers.update(config.default_headers)
        if config.auth_token: #may be api key
            headers["Authorization"] = f"Bearer {config.auth_token}"
        
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            headers=headers
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> httpx.Response:
        """Make HTTP request with rate limiting and error handling"""
        
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
                headers=request_headers
            )
            
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                logger.warning(f"Rate limited. Retry after {retry_after} seconds")
                raise RateLimitError(f"Rate limited: {response.status_code}")
            
           
            if response.status_code >= 500:
                raise ExternalServiceError(f"Server error: {response.status_code}")
            
            print("response status code: ",response.status_code)
            
            response.raise_for_status()
            return response
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error in {method} {endpoint}: {e}")
            raise ExternalServiceError(f"HTTP error: {e}")
    
    # @async_retry(max_attempts=3, wait_multiplier=2)
    # @circuit_breaker("external_api", failure_threshold=5, recovery_timeout=60.0)
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """GET request"""
        response = await self._make_request("GET", endpoint, params=params, headers=headers)
        return response.json()
    
    # @async_retry(max_attempts=3, wait_multiplier=2)
    # @circuit_breaker("external_api", failure_threshold=5, recovery_timeout=60.0)
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """POST request"""
        response = await self._make_request("POST", endpoint, data=data, headers=headers)
        return response.json() if response.content else {}
    
    @async_retry(max_attempts=3, wait_multiplier=2)
    @circuit_breaker("external_api", failure_threshold=5, recovery_timeout=60.0)
    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """PUT request"""
        response = await self._make_request("PUT", endpoint, data=data, headers=headers)
        return response.json() if response.content else {}
    
    @async_retry(max_attempts=3, wait_multiplier=2)
    @circuit_breaker("external_api", failure_threshold=5, recovery_timeout=60.0)
    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """DELETE request"""
        response = await self._make_request("DELETE", endpoint, headers=headers)
        return response.json() if response.content else None


class ApiClientFactory:
    _clients: Dict[str, ExternalApiClient] = {}
    
    @classmethod
    def create_client(cls, service_name: str, config: ApiClientConfig) -> ExternalApiClient:
        """Create and cache API client"""
        if service_name not in cls._clients:
            cls._clients[service_name] = ExternalApiClient(config)
        return cls._clients[service_name]
    
    @classmethod
    async def close_all(cls):
        """Close all cached clients"""
        for client in cls._clients.values():
            await client.client.aclose()
        cls._clients.clear()