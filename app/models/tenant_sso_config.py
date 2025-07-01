import enum
from sqlalchemy import UUID, DateTime, ForeignKey, Integer, Column, String, Text, JSON, Boolean, UniqueConstraint, func
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel, TenantIsolatedModel

class TenantSSOConfig(TenantIsolatedModel):

    __tablename__ = "tenant_sso_config"
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    provider = Column(String(255), nullable=False)
    provider_tenant_id = Column(UUID(as_uuid=True), nullable=True)
    client_id = Column(String, nullable=False)

    domain = Column(String(255), nullable=False)
    attribute_mappings = Column(JSONB, default=dict)
    role_mappings = Column(JSONB, default=dict)
