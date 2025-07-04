from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime

class TenantBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100, pattern="^[a-z0-9-]+$")
    domain: Optional[str] = Field(None, max_length=255)

class TenantCreate(TenantBase):
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)

class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)


class TenantResponse(TenantBase):
    id: UUID
    plan_type: str
    employee_count: int
    # sso_config: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True