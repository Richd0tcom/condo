import hmac
import hashlib
import json
from typing import Dict, Any, Optional, Callable, List
from fastapi import HTTPException, Header, Request
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from enum import Enum

logger = logging.getLogger(__name__)

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

class WebhookSignatureError(Exception):
    """Webhook signature verification failed"""
    pass

class WebhookTimestampError(Exception):
    """Webhook timestamp validation failed"""
    pass

class WebhookReceiver:
    def __init__(self):
        self.configs: Dict[WebhookSource, WebhookConfig] = {}
        self.processors: Dict[str, Callable] = {}
    
    def register_source(self, config: WebhookConfig):
        """Register a webhook source with its configuration"""
        self.configs[config.source] = config
        logger.info(f"Registered webhook source: {config.source.value}")
    
    def register_processor(self, event_type: str, processor: Callable):
        """Register a processor function for an event type"""
        self.processors[event_type] = processor
        logger.info(f"Registered processor for event type: {event_type}")
    
    async def verify_signature(
        self,
        payload: bytes,
        signature: str,
        config: WebhookConfig
    ) -> bool:
        """Verify webhook signature"""
        try:
            if "=" in signature:
                algorithm, signature = signature.split("=", 1)
            
            if config.signature_algorithm == "sha256":
                expected = hmac.new(
                    config.secret_key.encode(),
                    payload,
                    hashlib.sha256
                ).hexdigest()
            else:
                raise ValueError(f"Unsupported algorithm: {config.signature_algorithm}")
            
            return hmac.compare_digest(expected, signature)
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    def verify_timestamp(self, timestamp_str: str, max_age_seconds: int) -> bool:
        """Verify webhook timestamp is within acceptable range"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age = (now - timestamp).total_seconds()
            
            return 0 <= age <= max_age_seconds
            
        except Exception as e:
            logger.error(f"Timestamp verification error: {e}")
            return False
    
    async def process_webhook(
        self,
        request: Request,
        source: WebhookSource,
        signature: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> WebhookPayload:
        """Process incoming webhook request"""
        
        config = self.configs.get(source)
        if not config:
            raise HTTPException(status_code=400, detail=f"Unknown webhook source: {source.value}")
        
        body = await request.body()
        
        if signature and config.secret_key:
            if not await self.verify_signature(body, signature, config):
                raise WebhookSignatureError("Invalid webhook signature")
        
        if timestamp:
            if not self.verify_timestamp(timestamp, config.max_age_seconds):
                raise WebhookTimestampError("Webhook timestamp too old or invalid")
        
        try:
            raw_payload = json.loads(body.decode())
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")
        
        event_type = raw_payload.get("event_type", "unknown")
        event_id = raw_payload.get("event_id", "")
        event_timestamp = raw_payload.get("timestamp")
        tenant_id = raw_payload.get("tenant_id")
        data = raw_payload.get("data", {})
        
        if event_timestamp:
            try:
                parsed_timestamp = datetime.fromisoformat(event_timestamp.replace('Z', '+00:00'))
            except ValueError:
                parsed_timestamp = datetime.now(timezone.utc)
        else:
            parsed_timestamp = datetime.now(timezone.utc)
        
        webhook_payload = WebhookPayload(
            source=source,
            event_type=event_type,
            event_id=event_id,
            timestamp=parsed_timestamp,
            data=data,
            tenant_id=tenant_id,
            raw_payload=raw_payload
        )
        
        logger.info(f"Processed webhook: {source.value}/{event_type} - {event_id}")
        return webhook_payload
    
    def get_processor(self, event_type: str) -> Optional[Callable]:
        """Get processor function for event type"""
        return self.processors.get(event_type)

webhook_receiver = WebhookReceiver()

DEFAULT_WEBHOOK_CONFIGS = {
    WebhookSource.USER_MANAGEMENT: WebhookConfig(
        source=WebhookSource.USER_MANAGEMENT,
        secret_key="user_management_secret_key_change_in_production",
        signature_header="X-User-Signature"
    ),
    WebhookSource.PAYMENT_SERVICE: WebhookConfig(
        source=WebhookSource.PAYMENT_SERVICE,
        secret_key="payment_service_secret_key_change_in_production",
        signature_header="X-Payment-Signature"
    ),
    WebhookSource.COMMUNICATION_SERVICE: WebhookConfig(
        source=WebhookSource.COMMUNICATION_SERVICE,
        secret_key="communication_service_secret_key_change_in_production",
        signature_header="X-Comm-Signature"
    ),
}

for config in DEFAULT_WEBHOOK_CONFIGS.values():
    webhook_receiver.register_source(config)