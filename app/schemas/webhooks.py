from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
import uuid

from pydantic import BaseModel, Field

from app.models.webhooks import EventType

class EventStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class WebhookSource(Enum):
    USER_MANAGEMENT = "user_management"
    PAYMENT_SERVICE = "payment_service"
    COMMUNICATION_SERVICE = "communication_service"

@dataclass
class WebhookConfig:
    source: WebhookSource
    secret_key: str
    signature_header: str = "X-Signature"
    timestamp_header: str = "X-Timestamp"
    signature_algorithm: str = "sha256"
    max_age_seconds: int = 300  

@dataclass
class WebhookPayload:
    source: WebhookSource
    event_type: str
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]
    tenant_id: Optional[str] = None
    raw_payload: Optional[Dict[str, Any]] = None

@dataclass
class ProcessingResult:
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_after_seconds: Optional[int] = None


class WebhookEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    tenant_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signature: Optional[str] = None
