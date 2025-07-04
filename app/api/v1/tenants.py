from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog

from app.core.database import get_db, get_tenant_db
from app.schemas.tenant import TenantResponse, TenantUpdate
from app.services.tenant import TenantService
from app.api.deps import  get_current_tenant_admin, get_current_super_admin, get_current_user
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """List all tenants (Super Admin only)"""
    
    tenant_service = TenantService(db)
    tenants = tenant_service.get_all_tenants(skip=skip, limit=limit)
    
    logger.info("Tenants listed", 
               count=len(tenants),
               requested_by=current_user.id)
    
    return tenants

@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's tenant"""
    
    tenant_service = TenantService(db)
    tenant = tenant_service.get_tenant_by_id(current_user.tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant

@router.put("/current", response_model=TenantResponse)
async def update_current_tenant(
    tenant_data: TenantUpdate,
    current_user: User = Depends(get_current_tenant_admin),
    db: Session = Depends(get_tenant_db)
):
    """Update current tenant (Admin only)"""
    
    tenant_service = TenantService(db)
    tenant = tenant_service.update_tenant(
        tenant_id=current_user.tenant_id,
        tenant_data=tenant_data,
        updated_by_user_id=current_user.id
    )
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant

@router.delete("/current")
async def deactivate_current_tenant(
    current_user: User = Depends(get_current_tenant_admin),
    db: Session = Depends(get_db)
):
    """Deactivate current tenant (Admin only)"""
    
    tenant_service = TenantService(db)
    tenant = tenant_service.deactivate_tenant(
        tenant_id=current_user.tenant_id,
        deactivated_by_user_id=current_user.id
    )
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return {"message": "Tenant deactivated successfully"}

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant_by_id(
    tenant_id: str,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get tenant by ID (Super Admin only)"""
    
    tenant_service = TenantService(db)
    tenant = tenant_service.get_tenant_by_id(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant

@router.delete("/{tenant_id}")
async def deactivate_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Deactivate tenant by ID (Super Admin only)"""
    
    tenant_service = TenantService(db)
    tenant = tenant_service.deactivate_tenant(
        tenant_id=tenant_id,
        deactivated_by_user_id=current_user.id
    )
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return {"message": "Tenant deactivated successfully"}