from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey, Enum as SQLEnum, UniqueConstraint, func
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel

class AuthType(str, enum.Enum):
    PASSWORD = "password"
    SSO = "sso" 


class UserAuthScheme(BaseModel):
    """User model with auth scheme"""
    __tablename__ = "user_auth_scheme"
    
   
    user_id = Column(String(36), ForeignKey("users.id"))

    hashed_password = Column(String(255), nullable=False)
    
   
    auth_type = Column(String(255), default=AuthType.PASSWORD, nullable=False)
    

    is_deleted = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    
    tenant_id = Column(String(36), ForeignKey("tenants.id")) #neccessary?
    

    
    user = relationship("User", back_populates="users")

    # we should probably have a unique constraint on user_id+authscheme 
    

    

