from typing import List

import structlog
from app.core.database import get_db
from app.mock.mock_services import WebhookEvent
from app.models.webhooks import WebhookStatus
from app.tasks.webhook import process_webhook_event


logger = structlog.get_logger(__name__)

class DeadLetterQueueManager:
    """Manage failed webhook events"""
    
    def __init__(self):
        self.db = next(get_db())
    
    def get_dead_letter_events(self, limit: int = 100) -> List[WebhookEvent]:
        """Get events in dead letter queue"""
        return self.db.query(WebhookEvent).filter(
            WebhookEvent.status == WebhookStatus.DEAD_LETTER
        ).order_by(WebhookEvent.created_at.desc()).limit(limit).all()
    
    def requeue_event(self, event_id: str) -> bool:
        """Requeue a dead letter event for processing"""
        try:
            event = self.db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
            if not event or event.status != WebhookStatus.DEAD_LETTER:
                return False
            
            # Reset event for reprocessing
            event.status = WebhookStatus.PENDING
            event.retry_count = 0
            event.error_message = None
            event.last_attempted_at = None
            
            self.db.commit()
            
            # Queue for processing
            process_webhook_event.delay(event_id)
            
            logger.info(f"Requeued dead letter event {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error requeuing event {event_id}: {str(e)}")
            return False
    
    def archive_event(self, event_id: str) -> bool:
        """Archive a dead letter event (mark as permanently failed)"""
        try:
            event = self.db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
            if not event:
                return False
            
            event.status = WebhookStatus.ARCHIVED
            event.archived_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Archived dead letter event {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error archiving event {event_id}: {str(e)}")
            return False