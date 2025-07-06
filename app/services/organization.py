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
from app.schemas.tenant import TenantCreate
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
        
        try:

            new_org = Organization(
                name=org.org_name
            )

            self.db.add(new_org)
            self.db.flush()

            tenant = tservice.create_tenant_with_admin(TenantCreate(
                 name=new_org.name,
                 slug= org.slug,
                 domain= org.domain,
                 admin_password=org.admin_password,
                 admin_email=org.admin_email,
                 admin_first_name=org.admin_first_name,
                 admin_last_name=org.admin_last_name
            ))
            
            logger.info("Organization created with admin", 
                        org_id=new_org.id,
                        slug=tenant.slug,
                        admin_email=new_org.admin_email)
            
            return new_org
    

        except Exception as e:
                self.db.rollback()

                print("I errored here")
                logger.error("Failed to create organization", error=str(e))
                raise


    def get_organization_by_id(self, id: str):
        return self.db.query(Organization).filter(Organization.id == id).first()

    def create_tenants_for_organization(self, tenant: TenantCreate):
        try:
        
            tservice= TenantService(self.db)
            tenant = tservice.create_tenant_with_admin(tenant)

        except Exception as e:
                print("I errored here")
                logger.error("Failed to create tentant for organization", error=str(e))
                raise


    def update_organization_settings():
        pass




