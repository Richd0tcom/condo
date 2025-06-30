from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class OrgBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)

class OrgCreate(OrgBase): #handled by super_admin
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=8)
    admin_first_name: str = Field(..., min_length=1, max_length=100)
    admin_last_name: str = Field(..., min_length=1, max_length=100)

class OrgSettingsUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)

    features_enabled =Field(list)
    webhook_endpoints = Field(list)
    domain: Optional[str] = Field(None, max_length=255)
    settings: Optional[Dict[str, Any]] = None #move to different schema


class IntegrationStatus(BaseModel):
    enabled: bool
    last_sync: datetime


class OrganizationsResponse(OrgBase):
    id: str
    subscription_tier: str
    employee_limit: int
    features_enabled: List[str]
    webhook_endpoints: List[str]
    external_integrations: Dict[str, IntegrationStatus]
    created_at: datetime

    class Config:
        from_attributes = True