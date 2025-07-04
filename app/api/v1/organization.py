from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog

from app.core.database import get_db, get_tenant_db
from app.schemas.tenant import TenantResponse, TenantUpdate
from app.services.tenant import TenantService
from app.api.deps import  get_current_tenant_admin, get_current_super_admin, get_current_user
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()


def create_organization():
    pass


def create_tenants_for_organization():
    pass

def get_organization():
    pass

def get_all_tenants_in_organization():
    pass

def update_organization_settings():
    pass