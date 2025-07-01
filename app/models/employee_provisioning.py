from sqlalchemy import UUID, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel

class EmployeeProvisioning(BaseModel):
    __tablename__ = 'employee_provisioning'

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"))
    personal_info = Column(JSONB, nullable=False, default=dict)
    role_info = Column(JSONB, nullable=False,  default=dict)
    access_requirements = Column(JSONB, nullable=False,  default=dict)
    equipment_needs = Column(JSONB, nullable=False,  default=dict)
