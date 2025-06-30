from pydantic import BaseModel, EmailStr
from typing import List
from datetime import date



class EmployeeProvisioning(BaseModel):
    id: str
    personal_info: dict[str, any]
    role_info: dict[str, any]
    access_requirements: dict[str, any]
    equipment_needs: dict[str, any]

    class Config:
        from_attributes = True
