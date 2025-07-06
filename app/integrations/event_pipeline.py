import asyncio
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging
from app.integrations.processors import EventTypeProcessor
from app.integrations.webhook import WebhookPayload, WebhookSource
from app.core.database import get_db_session, get_async_db_session  # Import the context managers
from sqlalchemy.orm import Session
import hashlib
from app.models import Tenant, AuditLog, WebhookStatus
from app.models.webhooks import EventType, WebhookEventDB
from app.schemas.webhooks import ProcessingResult

logger = logging.getLogger(__name__)

class EventStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class EventProcessor:
    def __init__(self):
        self.processors = EventTypeProcessor().processors
        self.middleware: List[Callable] = []
        self.deduplication_cache: Dict[str, datetime] = {} #TODO: change to use redis
        self._lock = asyncio.Lock()
    
    def register_processor(self, event_type: str, processor: Callable):
        """Register an event processor function"""
        self.processors[event_type] = processor
        logger.info(f"Registered processor for event type: {event_type}")
    
    def add_middleware(self, middleware: Callable):
        """Add middleware to the processing pipeline"""
        self.middleware.append(middleware)
        logger.info(f"Added middleware: {middleware.__name__}")
    
    def generate_event_hash(self, payload: WebhookPayload) -> str:
        """Generate unique hash for event deduplication"""
        hash_data = f"{payload.event_id}:{payload.source.value}:{payload.timestamp.isoformat()}"
        return hashlib.sha256(hash_data.encode()).hexdigest()
    
    async def is_duplicate_event(self, payload: WebhookPayload) -> bool:
        """Check if event has already been processed (idempotency)"""
        event_hash = self.generate_event_hash(payload)
        
        async with self._lock:
            if event_hash in self.deduplication_cache:
                return True
            
            try:
                # Use context manager for manual database access
                with get_db_session() as db:
                    result = db.query(WebhookEventDB.id).filter(
                        WebhookEventDB.idempotency_key == event_hash
                    ).first()
                    
                    if result:
                        self.deduplication_cache[event_hash] = payload.timestamp
                        return True
            
            except Exception as e:
                logger.error(f"Error checking duplicate event: {e}")
                return False
            
            return False
    
    async def mark_event_processed(self, payload: WebhookPayload, result: ProcessingResult):
        """Mark event as processed in database and cache"""
        event_hash = self.generate_event_hash(payload)
        
        try:
            with get_db_session() as db:
                existing_event = db.query(WebhookEventDB).filter(
                    WebhookEventDB.idempotency_key == event_hash
                ).first()
                
                if existing_event:
                    existing_event.status = WebhookStatus.COMPLETED if result.success else WebhookStatus.FAILED
                    existing_event.processed_at = datetime.now(timezone.utc)
                    existing_event.data = result.metadata
                else:
                    new_event = WebhookEventDB(
                        # id=payload.event_id,
                        service_name=payload.source.value,
                        event_type=payload.event_type,
                        payload=payload.data,
                        tenant_id=payload.tenant_id,
                        idempotency_key=event_hash,
                        status=WebhookStatus.COMPLETED if result.success else WebhookStatus.FAILED,
                        error_message=result.error_message,
                        completed_at=datetime.now(timezone.utc)
                    )
                    db.add(new_event)
                # Commit happens automatically in context manager
            
            async with self._lock:
                self.deduplication_cache[event_hash] = payload.timestamp
                
                # Cache cleanup
                if len(self.deduplication_cache) > 1000:
                    oldest_keys = sorted(
                        self.deduplication_cache.keys(),
                        key=lambda k: self.deduplication_cache[k]
                    )[:500]
                    for key in oldest_keys:
                        del self.deduplication_cache[key]
        
        except Exception as e:
            logger.error(f"Error marking event as processed: {e}")
    
    async def apply_middleware(self, payload: WebhookPayload) -> WebhookPayload:
        """Apply middleware to the payload"""
        current_payload = payload
        
        for middleware in self.middleware:
            try:
                current_payload = await middleware(current_payload)
            except Exception as e:
                logger.error(f"Middleware {middleware.__name__} failed: {e}")
                raise
        
        return current_payload
    
    async def process_event(self, payload: WebhookPayload) -> ProcessingResult:
        """Process a webhook event through the pipeline"""
        
        if await self.is_duplicate_event(payload):
            logger.info(f"Duplicate event detected: {payload.event_id}")
            return ProcessingResult(
                success=True,
                metadata={"skipped": "duplicate_event"}
            )
        
        try:
            processed_payload = await self.apply_middleware(payload)
            
            
            processor = self.processors.get(processed_payload.event_type)
            if not processor:
                logger.warning(f"No processor found for event type: {processed_payload.event_type}")
                return ProcessingResult(
                    success=False,
                    error_message=f"No processor for event type: {processed_payload.event_type}"
                )
            
            logger.info(f"Processing event: {processed_payload.event_type} - {processed_payload.event_id}")
            result = await processor(processed_payload)

            print("Processing webhook 222222222...") 
            
            await self.mark_event_processed(payload, result)
            
            if result.success:
                logger.info(f"Successfully processed event: {processed_payload.event_id}")
            else:
                logger.error(f"Failed to process event: {processed_payload.event_id} - {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing event {payload.event_id}: {e}")
            result = ProcessingResult(
                success=False,
                error_message=str(e)
            )
            
            try:
                await self.mark_event_processed(payload, result)
            except Exception as mark_error:
                logger.error(f"Error marking failed event: {mark_error}")
            
            return result

event_processor = EventProcessor()

async def tenant_validation_middleware(payload: WebhookPayload) -> WebhookPayload:
    """Validate tenant information in webhook payload"""
    if payload.tenant_id:
        try:
            with get_db_session() as db:
                result = db.query(Tenant.id).filter(
                    Tenant.id == payload.tenant_id, 
                    # Tenant.is_active == True
                ).first()
                
                if not result:
                    raise ValueError(f"Invalid or inactive tenant: {payload.tenant_id}")
        
        except Exception as e:
            logger.error(f"Tenant validation failed: {e}")
            raise
    
    return payload

async def audit_logging_middleware(payload: WebhookPayload) -> WebhookPayload:
    """Log webhook events for audit purposes"""
    try:
        with get_db_session() as db:
            audit_entry = AuditLog(
                tenant_id=payload.tenant_id,
                event_type=f"webhook_received_{payload.event_type}",
                resource_type="webhook",
                
                data= {
                    "id": payload.event_id,
                    "source": payload.source.value,
                    "timestamp": payload.timestamp.isoformat()
                }
            )
            db.add(audit_entry)
            # Commit happens automatically in context manager

    except Exception as e:
        logger.error(f"Audit logging failed: {e}")
    
    return payload

event_processor.add_middleware(tenant_validation_middleware)
event_processor.add_middleware(audit_logging_middleware)