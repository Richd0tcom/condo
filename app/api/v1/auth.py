from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import structlog

from app.core.database import get_db
from app.core.security import create_access_token
from app.core.settings import settings
from app.models.user import User
from app.schemas.auth import Token, LoginRequest, RegisterRequest, UserProfile
from app.schemas.tenant import TenantCreate
from app.services.user import UserService
from app.services.tenant import TenantService
from app.api.deps import  get_current_user

logger = structlog.get_logger()
router = APIRouter()

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_tenant_and_admin(
    request: Request,
    registration_data: TenantCreate,
    db: Session = Depends(get_db)
):
    """Register new tenant with admin user"""
    
    try:
        tenant_service = TenantService(db)
        
        tenant = tenant_service.create_tenant_with_admin(registration_data)
        
        logger.info("Tenant registration", 
                   tenant_id=tenant.id,
                   slug=registration_data.slug,
                   admin_email=registration_data.admin_email,
                   ip_address=request.client.host)
        
        return {
            "message": "Tenant and admin user created successfully",
            "tenant_id": tenant.id,
            "slug": tenant.slug,
            "admin_email": registration_data.admin_email
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(e)
        logger.error("Registration failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    
    try:
        user_service = UserService(db)
        tenant_service = TenantService(db)
        
        tenant = None
        if login_data.tenant_slug:
            tenant = tenant_service.get_tenant_by_slug(login_data.tenant_slug)
        else:
            # Try to extract from host header (subdomain)
            host = request.headers.get("host", "")
            if "." in host:
                subdomain = host.split(".")[0]
                tenant = tenant_service.get_tenant_by_slug(subdomain)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant not found or not specified"
            )
        
        
        user = user_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
            tenant_id=tenant.id
        )
        
        if not user:
            logger.warning("Failed login attempt", 
                          email=login_data.email,
                          tenant_id=tenant.id,
                          ip_address=request.client.host)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_subject = f"{user.id}:{user.tenant_id}"  
        access_token = create_access_token(
            subject=token_subject,
            expires_delta=access_token_expires
        )
        
        logger.info("User login successful", 
                   user_id=user.id,
                   email=user.email,
                   tenant_id=user.tenant_id,
                   ip_address=request.client.host)
        
        return {
            "access_token": access_token,
            "user_info": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "tenant_id": user.tenant_id,
                "tenant_name": tenant.name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Logout user (client-side token invalidation)"""
    

    
    logger.info("User logout", 
               user_id=current_user.id,
               tenant_id=current_user.tenant_id,
               ip_address=request.client.host)
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return current_user

@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """Refresh JWT token"""
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_subject = f"{current_user.id}:{current_user.tenant_id}"
    access_token = create_access_token(
        subject=token_subject,
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }



