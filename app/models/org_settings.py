from sqlalchemy import ForeignKey, Integer, Column, String, Text, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import BaseModel

class OrganizationSettings(BaseModel):
    """Tenant/Organization model for multi-tenancy"""
    __tablename__ = "organization_settings"
    
    # Unique tenant identifier (UUID)
    id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    
    
    features_enabled = Column(JSONB, default=list)
    webhook_endpoints = Column(JSONB, default=list)


    organization_id = Column(String(36), ForeignKey("organizations.id"))


    __table_args__ = (
        UniqueConstraint('organiztion_id', name='uq_org_settings'),
    )