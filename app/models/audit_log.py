from sqlalchemy import UUID, Column, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import TenantIsolatedModel

class AuditLog(TenantIsolatedModel):
    """audit logging for compliance"""
    __tablename__ = "audit_logs"


    # CREATE, UPDATE, DELETE, LOGIN

    event_type = Column(String(100), nullable=False)  

    resource_type = Column(String(100), nullable=False) 
    resource_id = Column(UUID(as_uuid=True), nullable=True)  # ID of affected resource
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    user_email = Column(String(255), nullable=True)  
    
    ip_address = Column(String(45), nullable=True)  # support IPv6 
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    
    data = Column(JSONB, default=dict)
    
    user = relationship("User")