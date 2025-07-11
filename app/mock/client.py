import asyncio
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from contextlib import asynccontextmanager

import structlog

from .config import mock_service_config

logger = structlog.get_logger(__name__)

class ExternalServiceClient:
    """HTTP client for external service interactions with retry logic"""
    
    def __init__(self):
        self.config = mock_service_config
        self.client_config = {
            "timeout": httpx.Timeout(self.config.service_timeout),
            "limits": httpx.Limits(max_connections=100, max_keepalive_connections=20)
        }
    
    @asynccontextmanager
    async def get_client(self):
        """Get HTTP client with proper lifecycle management"""
        async with httpx.AsyncClient(**self.client_config) as client:
            yield client
    
    async def call_service(
        self,
        service_name: str,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP call to external service with retry logic"""
        
        service_urls = {
            "user_management": self.config.user_management_url,
            "payment": self.config.payment_service_url,
            "communication": self.config.communication_service_url
        }
        
        if service_name not in service_urls:
            logger.error(f"Unknown service: {service_name}")
            return None
        
        url = f"{service_urls[service_name]}{endpoint}"
        
        try:
            async with self.get_client() as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=data, headers=headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None
                
                response.raise_for_status()
                return response.json() if response.content else {}
                
        except httpx.TimeoutException:
            logger.error(f"Timeout calling {service_name} service: {url}")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling {service_name} service: {e.response.status_code} - {url}")
            
        except Exception as e:
            logger.error(f"Error calling {service_name} service: {str(e)} - {url}")
        
        # Retry logic
        if retry_count < self.config.max_retries:
            delay = min(
                self.config.retry_backoff_factor ** retry_count,
                self.config.retry_max_delay
            )
            await asyncio.sleep(delay)
            return await self.call_service(service_name, method, endpoint, data, headers, retry_count + 1)
        
        return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create user in external user management service"""
        return await self.call_service("user_management", "POST", "/users", user_data)
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user from external user management service"""
        return await self.call_service("user_management", "GET", f"/users/{user_id}")
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user in external user management service"""
        return await self.call_service("user_management", "PUT", f"/users/{user_id}", user_data)
    
    async def delete_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Delete user from external user management service"""
        return await self.call_service("user_management", "DELETE", f"/users/{user_id}")
    
    async def create_subscription(self, subscription_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create subscription in payment service"""
        return await self.call_service("payment", "POST", "/subscriptions", subscription_data)
    
    async def process_payment(self, payment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process payment in payment service"""
        return await self.call_service("payment", "POST", "/payments/process", payment_data)
    
    async def send_notification(self, notification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send notification via communication service"""
        return await self.call_service("communication", "POST", "/notifications/send", notification_data)
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all external services"""
        services = ["user_management", "payment", "communication"]
        results = {}
        
        for service in services:
            try:
                result = await self.call_service(service, "GET", "/health")
                results[service] = result is not None and result.get("status") == "healthy"
            except:
                results[service] = False
        
        return results

# Global client instance
external_client = ExternalServiceClient()