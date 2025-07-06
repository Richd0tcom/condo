from random import randint
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import pytz
import structlog

from app.core.settings import settings
from app.core.database import get_db, get_tenant_db
from app.integrations.external_client import ApiClientConfig, ExternalApiClient
from app.schemas.tenant import TenantResponse, TenantUpdate
from app.services.tenant import TenantService
from app.api.deps import (
    get_current_tenant_admin,
    get_current_super_admin,
    get_current_user,
)
from app.models.user import User


timezone_name = "Africa/Lagos"
tz = pytz.timezone(timezone_name)

logger = structlog.get_logger()
router = APIRouter()


@router.post("/users", response_model=dict, status_code=status.HTTP_201_CREATED)
async def call_external_user_service(db: Session = Depends(get_db)):

    config = ApiClientConfig(
        base_url=settings.EXTERNAL_USER_SERVICE_URL,
    )

    try:
        users = db.query(User).all()

        user = users[randint(0, len(users) - 1)]

        data = {
            "id": user.id.__str__(),
            "name": user.full_name,
            "email": user.email,
            "tenant_id": user.tenant_id.__str__(),
        }

        client = ExternalApiClient(config)
        response = await client.post("/users", data=data)
        print("ressssyyyy",response)
        return response

    except Exception as e:
        logger.error("Failed to call external user service", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to call external user service",
        )


@router.post("/payment", response_model=dict, status_code=status.HTTP_201_CREATED)
def call_external_payment_service(db: Session = Depends(get_db)):
    config = ApiClientConfig(
        base_url=settings.EXTERNAL_PAYMENT_SERVICE_URL,
    )
    client = ExternalApiClient(config)

    try:
        users = db.query(User).all()

        user = users[randint(0, len(users) - 1)]

        data = {
          "tenant_id": user.tenant_id.__str__(),
          "user_id": user.id.__str__(),
          "plan_id": "1",
          "status": "active",
          "amount": 100,
          "currency": "USD",
          "billing_cycle": "monthly",
          "current_period_start": datetime.now(tz),
          "current_period_end": datetime.now(tz) + timedelta(days=30),
          "created_at": datetime.now(tz),
        }

        response = client.post("/subscriptions", data=data)

        payment_data = {
            "subscription_id": response.id,
            "amount": data.amount,
            "currency": data.get("currency", "USD"),
            "tenant_id": user.tenant_id
        }

        response = client.post("/payments/process", data=payment_data)
        return response

    except Exception as e:
        logger.error("Failed to call external payment service", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to call external payment service",
        )


@router.post("/notifications", response_model=dict, status_code=status.HTTP_201_CREATED)
def call_external_comms_service(db: Session = Depends(get_db)):
    config = ApiClientConfig(
        base_url=settings.EXTERNAL_COMMS_SERVICE_URL,
    )
    client = ExternalApiClient(config)

    try:
        users = db.query(User).all()

        user = users[randint(0, len(users) - 1)]

        data = {
            "tenant_id": user.tenant_id,
            "user_id": user.id,
            "type": "email",
            "recipient": user.email,
            "subject": "Test Email",
            "content": "This is a test email",
            "status": "pending"
        }

        response = client.post("/notifications/send", data=data)
        return response

    except Exception as e:
        logger.error("Failed to call external comms service", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to call external comms service",
        )
