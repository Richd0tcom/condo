from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
import structlog
import uuid

from app.models.auth_schema import UserAuthScheme
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.core.security import get_password_hash

logger = structlog.get_logger()

class TenantService:
    """Enterprise tenant management service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by tenant_id"""
        return self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug"""
        return self.db.query(Tenant).filter(Tenant.slug == slug).first()
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by custom domain"""
        return self.db.query(Tenant).filter(Tenant.domain == domain).first()
    
    def get_all_tenants(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """Get all tenants with pagination (super admin only)"""
        return self.db.query(Tenant).offset(skip).limit(limit).all()
    
    def create_tenant_with_admin(self, tenant_data: TenantCreate) -> Tenant:
        """Create tenant with initial admin user"""
        

        existing_tenant = self.get_tenant_by_slug(tenant_data.slug)
        if existing_tenant:
            raise ValueError("Tenant with this slug already exists")
        

        if tenant_data.domain:
            existing_domain = self.get_tenant_by_domain(tenant_data.domain)
            if existing_domain:
                raise ValueError("Tenant with this domain already exists")
        
        try:

            db_tenant = Tenant(
                name=tenant_data.name,
                slug=tenant_data.slug,
                domain=tenant_data.domain
            )
            
            self.db.add(db_tenant)
            self.db.flush()  # Get ID without committing
            
            

            admin_user = User(
                email=tenant_data.admin_email,
                
                first_name=tenant_data.admin_first_name,
                last_name=tenant_data.admin_last_name,
                role=UserRole.TENANT_ADMIN,
                tenant_id=db_tenant.id,
                is_verified=True  # Auto-verify admin user
            )

            self.db.add(admin_user)
            self.db.flush()

            
            auth_scheme = UserAuthScheme(
                user_id=admin_user.id,
                hashed_password=get_password_hash(tenant_data.admin_password),
            )
            
            self.db.add(auth_scheme)
            self.db.flush()            
            
            

            
            audit_log = AuditLog(
                event_type="CREATE",
                resource_type="Tenant",
                resource_id=str(db_tenant.id),
                user_id=admin_user.id,
                tenant_id=db_tenant.id,
                new_values={
                    "name": tenant_data.name,
                    "slug": tenant_data.slug,
                    "domain": tenant_data.domain,
                    "admin_email": tenant_data.admin_email
                }
            )
            
            self.db.add(audit_log)

            
            self.db.commit()
            self.db.refresh(db_tenant)
            
            logger.info("Tenant created with admin", 
                       tenant_id=db_tenant.id,
                       slug=tenant_data.slug,
                       admin_email=tenant_data.admin_email)
            
            return db_tenant
            
        except Exception as e:
            self.db.rollback()

            print("I errored here")
            logger.error("Failed to create tenant", error=str(e))
            raise
    
    def update_tenant(self, tenant_id: str, tenant_data: TenantUpdate, updated_by_user_id: int) -> Optional[Tenant]:
        """Update tenant with audit logging"""
        
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return None
        

        old_values = {
            "name": tenant.name,
            "domain": tenant.domain,
            "settings": tenant.settings,
            "max_users": tenant.max_users
        }
        

        update_data = tenant_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)
        

        audit_log = AuditLog(
            event_type="UPDATE",
            resource_type="Tenant",
            resource_id=str(tenant.id),
            user_id=updated_by_user_id,
            tenant_id=tenant_id,
            old_values=old_values,
            new_values=update_data
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(tenant)
        
        logger.info("Tenant updated", 
                   tenant_id=tenant_id,
                   updated_by=updated_by_user_id,
                   changes=update_data)
        
        return tenant
    
    #protect
    def deactivate_tenant(self, tenant_id: str, deactivated_by_user_id: int) -> Optional[Tenant]:
        """Deactivate tenant (soft delete)"""
        
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return None
        
        tenant.is_active = False
        
        self.db.query(User).filter(User.tenant_id == tenant_id).update({"is_active": False})
        

        audit_log = AuditLog(
            event_type="DEACTIVATE",
            resource_type="Tenant",
            resource_id=str(tenant.id),
            user_id=deactivated_by_user_id,
            tenant_id=tenant_id,
            old_values={"is_active": True},
            new_values={"is_active": False}
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        logger.warning("Tenant deactivated", 
                      tenant_id=tenant_id,
                      deactivated_by=deactivated_by_user_id)
        
        return tenant