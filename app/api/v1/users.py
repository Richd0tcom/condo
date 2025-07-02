from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
import structlog

from app.core.database import get_db
from app.schemas.user import UserResponse, UserCreate, UserUpdate, PasswordChange
from app.services.user import UserService
from app.api.deps import get_current_tenant_admin, get_current_user
from app.models.user import User
from app.core.security import verify_password, get_password_hash

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_tenant_admin),
    db: Session = Depends(get_db)
):
    """List users in current tenant (Admin only)"""
    
    user_service = UserService(db)
    users = user_service.get_users_by_tenant(
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )
    
    logger.info("Users listed", 
               tenant_id=current_user.tenant_id,
               count=len(users),
               requested_by=current_user.id)
    
    return users

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_tenant_admin),
    db: Session = Depends(get_db)
):
    """Create new user in current tenant (Admin only)"""
    
    try:
        user_service = UserService(db)
        user = user_service.create_user(
            user_data=user_data,
            tenant_id=current_user.tenant_id,
            created_by_user_id=current_user.id
        )
        
        return user
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_tenant_admin),
    db: Session = Depends(get_db)
):
    """Get user by ID within current tenant (Admin only)"""
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id, current_user.tenant_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_tenant_admin),
    db: Session = Depends(get_db)
):
    """Update user within current tenant (Admin only)"""
    
    user_service = UserService(db)
    user = user_service.update_user(
        user_id=user_id,
        user_data=user_data,
        tenant_id=current_user.tenant_id,
        updated_by_user_id=current_user.id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    logger.info("Password changed", 
               user_id=current_user.id,
               tenant_id=current_user.tenant_id)
    
    return {"message": "Password changed successfully"}

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile"""
    
    allowed_fields = {"first_name", "last_name"}
    update_data = {k: v for k, v in profile_data.model_dump(exclude_unset=True).items() 
                   if k in allowed_fields}
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    logger.info("Profile updated", 
               user_id=current_user.id,
               changes=update_data)
    
    return current_user