from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
import structlog
import uuid

from app.core.database import get_db, get_org_db
from app.core.security import get_password_hash
from app.models.audit_log import AuditLog
from app.models.auth_schema import UserAuthScheme
from app.models.organization import Organization
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.schemas.organization import CreateOrganization
from app.services.tenant import TenantService
logger = structlog.get_logger()




class OrganizationService:

    def __init__(self, db: Session):
        self.db = db


    def create_organization(self, org: CreateOrganization):
        existing_org = self.db.query(Organization).filter(Organization.name == org.org_name).first()
        
        if existing_org:
            raise ValueError("org name already exists")
        
        tservice= TenantService(self.db)
        existing_org_tenant = tservice.get_tenant_by_domain(org.domain)

        if existing_org_tenant:
            raise ValueError("org with this domain already exists")

        new_org = Organization(
            name=org.org_name
        )

        self.db.add(new_org)
        self.db.flush()

        tenant = Tenant(
            domain=org.domain,
            slug = org.slug,
            name=f"{org.org_name}-default" 
        )
        self.db.add(tenant)
        self.db.flush()


        admin_user = User(
            email=org.admin_email,
            
            first_name=org.admin_first_name,
            last_name=org.admin_last_name,
            role=UserRole.TENANT_ADMIN,
            tenant_id=tenant.id,
            is_verified=True  # Auto-verify admin user
        )

        self.db.add(admin_user)
        self.db.flush()

        
        auth_scheme = UserAuthScheme(
            user_id=admin_user.id,
            hashed_password=get_password_hash(org.admin_password),
        )
        
        self.db.add(auth_scheme)
        self.db.flush()            
        
        
        audit_log = AuditLog(
            event_type="CREATE",
            resource_type="Organization",
            resource_id=str(new_org.id),
            user_id=admin_user.id,
            tenant_id=tenant.id,
            new_values={
                "name": new_org.name,
                "slug": tenant.slug,
                "domain": tenant.domain,
                "admin_email": admin_user.email
            }
        )
        
        self.db.add(audit_log)

        
        self.db.commit()
        self.db.refresh(new_org)
        
        logger.info("Organization created with admin", 
                    org_id=new_org.id,
                    slug=tenant.slug,
                    admin_email=new_org.admin_email)
        
        return new_org




    def get_organization_by_id(self, id: str):
        return self.db.query(Organization).filter(Organization.id == id).first()

    def create_tenants_for_organization():
        pass

    def update_organization_settings():
        pass




