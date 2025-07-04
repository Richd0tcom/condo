from fastapi import APIRouter

from app.api.v1 import auth, tenants, users, organization

api_router = APIRouter()


api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(organization.router, prefix="/organization", tags=["Organization"])