from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
import time
import redis
import json
import structlog
from typing import Callable
import traceback

from app.core.settings import settings

logger = structlog.get_logger()


class AuditMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware for compliance"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        
        request_data = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "timestamp": time.time()
        }
        
        try:
            response = await call_next(request)
            
            duration = time.time() - start_time
            logger.info("API Request", 
                       **request_data,
                       status_code=response.status_code,
                       duration=duration,
                       tenant_id=getattr(request.state, 'tenant_id', None),
                       user_id=getattr(request.state, 'user_id', None))
            
            return response
            
        except Exception as e:
            
            duration = time.time() - start_time
            logger.error("API Request Failed",
                        **request_data,
                        error=str(e),
                        traceback=traceback.format_exc(),
                        duration=duration)
            raise

class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to inject tenant context into requests"""
    
    async def dispatch(self, request: Request, call_next: Callable):
        
        tenant_id = None
        
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["www", "api"]: 
                
                pass
        
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            tenant_id = tenant_header
        
        # OR From JWT token (will be set by auth dependency)
        
        request.state.tenant_id = tenant_id
        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enterprise-grade rate limiting middleware"""
    
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis_client = redis_client
        self.rate_limit = settings.RATE_LIMIT_PER_MINUTE
    
    async def dispatch(self, request: Request, call_next: Callable):
        client_ip = request.client.host
        user_id = getattr(request.state, 'user_id', None)
        client_key = f"rate_limit:{client_ip}:{user_id or 'anonymous'}"
        
        try:
            current_requests = self.redis_client.get(client_key)
            if current_requests is None:
                self.redis_client.setex(client_key, 60, 1)  # 1 minute window
            else:
                current_count = int(current_requests)
                if current_count >= self.rate_limit:
                    logger.warning("Rate limit exceeded", 
                                 client_ip=client_ip, 
                                 user_id=user_id,
                                 count=current_count)
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Rate limit exceeded. Try again later."}
                    )
                self.redis_client.incr(client_key)
        except redis.RedisError as e:
            logger.error("Redis error in rate limiting", error=str(e))
        
        response = await call_next(request)
        return response