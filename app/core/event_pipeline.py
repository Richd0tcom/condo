import asyncio
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import logging

import structlog
from app.integrations.webhook import WebhookPayload, WebhookSource
from app.core.database import get_db_session, get_async_db_session  # Import the context managers
from sqlalchemy.orm import Session
import hashlib
from app.models import Tenant, AuditLog, WebhookStatus
from app.models.webhooks import EventType, WebhookEventDB
from app.schemas.webhooks import ProcessingResult
from pymitter import EventEmitter

logger = structlog.get_logger(__name__)

event_emitter = EventEmitter()

class EventPipeline:
    def __init__(self, emitter: EventEmitter):
        self.emmiter = emitter
        self.middleware: List[Callable] = []
        self.deduplication_cache: Dict[str, datetime] = {} #TODO: change to use redis
        self._lock = asyncio.Lock()

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
            
            async with self._lock:
                self.deduplication_cache[event_hash] = payload.timestamp
                
                if len(self.deduplication_cache) > 1000:
                    oldest_keys = sorted(
                        self.deduplication_cache.keys(),
                        key=lambda k: self.deduplication_cache[k]
                    )[:500]
                    for key in oldest_keys:
                        del self.deduplication_cache[key]
        
        except Exception as e:
            logger.error(f"Error marking event as processed: {e}")

    

processing_pipeline = EventPipeline(event_emitter)


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

processing_pipeline.add_middleware(tenant_validation_middleware)
processing_pipeline.add_middleware(audit_logging_middleware)