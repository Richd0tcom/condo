from sqlalchemy import UUID, Column, Integer, DateTime, String, Boolean, Text, text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base, declared_attr
import uuid

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields for all entities"""
    __abstract__ = True

    __allow_unmapped__ = True
    
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, server_default=text("gen_random_uuid()"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class TenantIsolatedModel(BaseModel):
    """Base model for tenant-isolated entities"""
    __abstract__ = True
    __allow_unmapped__ = True
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # UUID as string for tenant isolation
    
    def __init__(self, **kwargs):
        # Ensure tenant_id is always set
        if 'tenant_id' not in kwargs:
            raise ValueError("tenant_id is required for tenant-isolated models")
        super().__init__(**kwargs)