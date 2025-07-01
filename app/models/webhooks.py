from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enum import Enum

from app.core.database import Base
from app.models.base import BaseModel

class WebhookStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    ARCHIVED = "archived"

class EventType(str, Enum):
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    PAYMENT_SUCCESS = "payment.success"
    PAYMENT_FAILED = "payment.failed"
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    EMAIL_DELIVERED = "email.delivered"
    EMAIL_BOUNCED = "email.bounced"
    EMAIL_FAILED = "email.failed"

class WebhookEvent(BaseModel):
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, index=True)
    service_name = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    tenant_id = Column(String, nullable=True, index=True)
    idempotency_key = Column(String, nullable=False, unique=True, index=True)
    status = Column(SQLEnum(WebhookStatus), default=WebhookStatus.PENDING, index=True)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    

    last_attempted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)