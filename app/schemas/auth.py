from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Union
from datetime import datetime

class TokenData(BaseModel):
    username: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None

class Token(BaseModel):
    access_token: str
    user_info: dict

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    tenant_slug: Optional[str] = None  # For multi-tenant login, will mostlikely be gotten from domain

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    tenant_slug: str = Field(..., min_length=3, max_length=100, pattern="^[a-z0-9-]+$") # will mostlikely be gotten from domain


class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    tenant_id: Union[UUID, str]
    created_at: datetime
    
    class Config:
        from_attributes = True