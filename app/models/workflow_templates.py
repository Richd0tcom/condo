from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel

class WorkflowTemplate(BaseModel):
    __tablename__ = 'workflow_templates'

    name = Column(String, nullable=False)
    description = Column(String)
    steps = Column(JSONB, nullable=False,  default=dict)
    estimated_duration_in_minutes = Column(Integer)
    requires_approval = Column(Boolean, default=False)
