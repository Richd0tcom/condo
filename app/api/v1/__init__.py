from fastapi import APIRouter

from app.api.v1 import auth, external, tenants, users, organization, webhooks

api_router = APIRouter()


api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(organization.router, prefix="/organization", tags=["Organization"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(external.router, prefix="/external", tags=["External"])