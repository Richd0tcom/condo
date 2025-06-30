from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class WorkflowTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[Dict[str, Any]]
    estimated_duration_in_minutes: int
    requires_approval: bool = False

    class Config:
        from_attributes = True

class WorkflowTemplateCreate(WorkflowTemplateBase):
    pass


    
