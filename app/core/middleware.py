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
                # Look up tenant by subdomain (implement in service layer)
                pass
        
        tenant_header = request.headers.get("X-Tenant-ID")
        if tenant_header:
            tenant_id = tenant_header
        
        # Method 3: From JWT token (will be set by auth dependency)
        # This will be handled in the auth dependency
        
        request.state.tenant_id = tenant_id
        response = await call_next(request)
        return response