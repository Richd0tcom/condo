from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Generator
import redis
import structlog

from app.core.database import get_db, get_tenant_db
from app.core.security import verify_token
from app.core.settings import settings
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.services.user import UserService
from app.services.tenant import TenantService

logger = structlog.get_logger()
security = HTTPBearer()

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_redis() -> redis.Redis:
    """Get Redis client"""
    return redis_client

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_tenant_db)
) -> User:
    """Get current authenticated user with tenant context"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print("creddiiii", credentials.credentials)
        token_data = verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
        
        user_id = str(token_data.split(":")[0])  # Format: "user_id:tenant_id"
        tenant_id = token_data.split(":")[1]
        
        user_service = UserService(db)
        user = user_service.get_user_auth_by_id(user_id, tenant_id)
        
        
        if user is None:
            print("userrrr", user)
            raise credentials_exception
        


        if user.auth_scheme.is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="User account is locked"
            )  

        # check user session from cache
        is_active = True
        if not is_active: #this is a place holder
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
            

        
        request.state.user_id = user.id
        request.state.tenant_id = user.tenant_id
        request.state.user_role = user.role
        
        logger.info("User authenticated", 
                   user_id=user.id, 
                   tenant_id=user.tenant_id,
                   role=user.role)
        
        return user
        
    except (ValueError, IndexError):
        raise credentials_exception
    except Exception as e:
        logger.error("Authentication error", error=str(e))
        raise credentials_exception


async def get_current_tenant_admin(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> User:
    """Require tenant admin or super admin role"""
    if current_user.role not in [UserRole.TENANT_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required."
        )
    if current_user.role == UserRole.SUPER_ADMIN:
        request.state.is_super_admin = 'true'

    return current_user

async def get_current_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require super admin role"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Super admin role required."
        )
    return current_user

def get_tenant_context(
    request: Request,
    db: Session = Depends(get_tenant_db)
) -> Optional[Tenant]:
    """Get tenant context from request"""
    tenant_id = getattr(request.state, 'tenant_id', None)
    if not tenant_id:
        return None
    
    tenant_service = TenantService(db)
    return tenant_service.get_tenant_by_id(tenant_id)


