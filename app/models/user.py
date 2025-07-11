from sqlalchemy import UUID, Column, Integer, String, Boolean, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
import enum

from app.models.auth_schema import UserAuthScheme
from app.models.base import TenantIsolatedModel

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin" 
    USER = "user"
    READONLY = "readonly"
    #we may add guests here

class User(TenantIsolatedModel):
    """User model with tenant isolation"""
    __tablename__ = "users"
    
   
    email = Column(String(255), nullable=False, index=True)
    
    
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
   
    role = Column(String(255), default=UserRole.USER, nullable=False)
    

    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)


    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))

    auth_scheme: UserAuthScheme = relationship("UserAuthScheme")
    
    __table_args__ = (
        UniqueConstraint('email', 'tenant_id', name='uq_user_email_tenant'),
    )
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
