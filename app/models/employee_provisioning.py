from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel

class EmployeeProvisioning(BaseModel):
    __tablename__ = 'employee_provisioning'

    id = Column(String, primary_key=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id"))
    personal_info = Column(JSONB, nullable=False)
    role_info = Column(JSONB, nullable=False)
    access_requirements = Column(JSONB, nullable=False)
    equipment_needs = Column(JSONB, nullable=False)
