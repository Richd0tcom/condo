import enum
from sqlalchemy import DateTime, ForeignKey, Integer, Column, String, Text, JSON, Boolean, UniqueConstraint, func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import BaseModel

class IntegrationType(str, enum.Enum):
    USER_SERVICE = "user_service"
    COMMS_SERVICE = "communications_service"
    PAYMENTS_SERVICE = "payments_service" 

class OrganizationIntegrations(BaseModel):

    __tablename__ = "organization_integrations"
    
    # Unique tenant identifier (UUID)
    id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)
    integration_type = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)
    
    last_sync = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    organization_id = Column(String(36), ForeignKey("organizations.id"))


