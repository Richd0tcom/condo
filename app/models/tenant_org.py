import enum
from sqlalchemy import UUID, DateTime, ForeignKey, Integer, Column, String, Text, JSON, Boolean, UniqueConstraint, func
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel, TenantIsolatedModel

class OrganizationTenants(BaseModel):

    __tablename__ = "organization_tenants"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))

    __table_args__ = (
        UniqueConstraint('organization_id', 'tenant_id', name='uq_org_tenant'),
    )


