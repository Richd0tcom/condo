from sqlalchemy import Integer, Column, String, Text, JSON, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid

from app.models.base import BaseModel

class Organization(BaseModel):
    """Tenant/Organization model for multi-tenancy"""
    __tablename__ = "organizations"
    
 
    name = Column(String(255), nullable=False)
    subscription_tier = Column(String(50), default="basic")
    employee_limit = Column(Integer, default=10) 

    #TODO:  create relationship for integrations and settings
    
