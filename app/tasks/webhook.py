from celery import Task
from app.core.database import get_db
from sqlalchemy import text
from datetime import timedelta

from app.tasks.celery import celery_app
from app.integrations.webhook import WebhookPayload, WebhookSource
from app.integrations.event_pipeline import event_processor, ProcessingResult
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class CallbackTask(Task):
    """Custom Celery task with callbacks for success/failure"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Task {task_id} retrying: {exc}")

@celery_app.task(bind=True, base=CallbackTask, name="process_webhook_event")
def process_webhook_event(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process webhook event asynchronously"""
    
    try:
        payload = WebhookPayload(
            source=WebhookSource(webhook_data["source"]),
            event_type=webhook_data["event_type"],
            event_id=webhook_data["event_id"],
            timestamp=datetime.fromisoformat(webhook_data["timestamp"]),
            data=webhook_data["data"],
            tenant_id=webhook_data.get("tenant_id"),
            raw_payload=webhook_data.get("raw_payload")
        )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(event_processor.process_event(payload))
        finally:
            loop.close()
        
        return {
            "success": result.success,
            "error_message": result.error_message,
            "metadata": result.metadata,
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error processing webhook event: {exc}")
        
        # exponential backoff this thing fit no work o
        if self.request.retries < self.max_retries:
            retry_countdown = 2 ** self.request.retries
            raise self.retry(exc=exc, countdown=retry_countdown)
        
        return {
            "success": False,
            "error_message": str(exc),
            "metadata": {"max_retries_reached": True},
            "processed_at": datetime.now(timezone.utc).isoformat()
        }

@celery_app.task(bind=True, name="process_bulk_webhook_events")
def process_bulk_webhook_events(self, webhook_events: list) -> Dict[str, Any]:
    """Process multiple webhook events in batch"""
    
    results = []
    successful = 0
    failed = 0
    
    for webhook_data in webhook_events:
        try:
            result = process_webhook_event.apply(args=[webhook_data])
            results.append(result.get())
            
            if result.get().get("success"):
                successful += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"Error in bulk processing: {e}")
            failed += 1
            results.append({
                "success": False,
                "error_message": str(e),
                "metadata": {"bulk_processing_error": True}
            })
    
    return {
        "total_processed": len(webhook_events),
        "successful": successful,
        "failed": failed,
        "results": results,
        "processed_at": datetime.now(timezone.utc).isoformat()
    }

@celery_app.task(name="cleanup_processed_events")
def cleanup_processed_events(days_to_keep: int = 30) -> Dict[str, Any]:
    """Clean up old processed events from database"""
    
    try:

        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def cleanup():
            async with get_db() as session:
                result = await session.execute(
                    text("DELETE FROM processed_events WHERE processed_at < :cutoff_date"),
                    {"cutoff_date": cutoff_date}
                )
                await session.commit()
                return result.rowcount
        
        try:
            deleted_count = loop.run_until_complete(cleanup())
        finally:
            loop.close()
        
        logger.info(f"Cleaned up {deleted_count} old processed events")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up processed events: {e}")
        return {
            "success": False,
            "error_message": str(e)
        }

@celery_app.task(name="periodic_cleanup")
def periodic_cleanup():
    """Periodic cleanup task"""
    return cleanup_processed_events.delay(days_to_keep=30)