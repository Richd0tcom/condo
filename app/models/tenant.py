from sqlalchemy import Integer, Column, String, Text, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid

from app.models.base import BaseModel

class Tenant(BaseModel):
    """Tenant/Organization model for multi-tenancy"""
    __tablename__ = "tenants"
    
    
    
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=True)  
    
    plan_type = Column(String(50), default="basic")
    employee_count = Column(Integer, default=10) 
    
    
    is_verified = Column(Boolean, default=False)
    # is_active = Column(Boolean, default=False)
  
    users = relationship("User", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('slug', name='uq_tenant_slug'),
        UniqueConstraint('domain', name='uq_tenant_domain'),
    )
