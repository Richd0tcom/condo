from datetime import datetime
import logging
from typing import List

import structlog

from app.core.database import get_db
from app.decorators.event_handler import event_handler
from app.mock.mock_services import WebhookEvent
from app.models.webhooks import EventType, WebhookEventDB, WebhookStatus
from app.schemas.webhooks import ProcessingResult, WebhookPayload

logger = structlog.get_logger()


"""Process different types of webhook events"""

@event_handler(EventType.USER_CREATED.value)
async def process_user_created(self, event: WebhookPayload) -> bool:
    """Process user creation event"""
    try:
        payload = event.data

        logger.info(f"Recorded successful user createion {payload['id']} for tenant {payload['tenant_id']}")
        return ProcessingResult(
                success=True,
            )
        
        
    except Exception as e:
        logger.error(f"Error processing user_created event: {str(e)}")
        return ProcessingResult(
                success=False,
            )

@event_handler(EventType.USER_UPDATED.value)
def process_user_updated(self, event: WebhookEvent) -> bool:
    """Process user update event"""
    try:
        payload = event.data
        logger.info(f"Recorded successful user  for tenant {payload['tenant_id']}")
        return True
            
    except Exception as e:
        logger.error(f"Error processing user_updated event: {str(e)}")
        return False
    


@event_handler(EventType.PAYMENT_SUCCESS.value)
def process_payment_success(self, event: WebhookEvent) -> bool:
    """Process successful payment event"""
    try:
        payload = event.payload
        
        logger.info(f"Recorded successful payment {payload['payment_id']} for tenant {payload['tenant_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing payment_success event: {str(e)}")
        return False

@event_handler(EventType.PAYMENT_FAILED.value)
def process_payment_failed(self, event: WebhookEvent) -> bool:
    """Process failed payment event"""
    try:
        payload = event.payload
        
        logger.info(f"Recorded failed payment {payload['payment_id']} for tenant {payload['tenant_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing payment_failed event: {str(e)}")
        return False

@event_handler(EventType.SUBSCRIPTION_CREATED.value)
def process_subscription_created(self, event: WebhookEvent) -> bool:
    """Process subscription creation event"""
    try:
        payload = event.payload
        
        logger.info(f"Created subscription {payload['subscription_id']} for tenant {payload['tenant_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing subscription_created event: {str(e)}")
        return False

@event_handler(EventType.EMAIL_DELIVERED.value)
def process_email_delivered(self, event: WebhookEvent) -> bool:
    """Process email delivery event"""
    try:
        payload = event.payload
        
        logger.info(f"Recorded email delivery {payload['message_id']} for tenant {payload['tenant_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing email_delivered event: {str(e)}")
        return False

@event_handler(EventType.EMAIL_BOUNCED.value)
def process_email_bounced(self, event: WebhookEvent) -> bool:
    """Process email bounce event"""
    try:
        payload = event.payload
        
        logger.info(f"Recorded email bounce {payload['message_id']} for tenant {payload['tenant_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing email_bounced event: {str(e)}")
        return False


# Dead Letter Queue Manager
# class DeadLetterQueueManager:
#     """Manage failed webhook events"""

#     def __init__(self):
#         self.db = next(get_db())

#     def get_dead_letter_events(self, limit: int = 100) -> List[WebhookEvent]:
#         """Get events in dead letter queue"""
#         return self.db.query(WebhookEvent).filter(
#             WebhookEvent.status == WebhookStatus.DEAD_LETTER
#         ).order_by(WebhookEvent.created_at.desc()).limit(limit).all()

#     def requeue_event(self, event_id: str) -> bool:
#         """Requeue a dead letter event for processing"""
#         try:
#             event = self.db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
#             if not event or event.status != WebhookStatus.DEAD_LETTER:
#                 return False
        
#             # Reset event for reprocessing
#             event.status = WebhookStatus.PENDING
#             event.retry_count = 0
#             event.error_message = None
#             event.last_attempted_at = None
        
#             self.db.commit()
        
#             # Queue for processing
#             process_webhook_event.delay(event_id)
        
#             logger.info(f"Requeued dead letter event {event_id}")
#             return True
        
#         except Exception as e:
#             logger.error(f"Error requeuing event {event_id}: {str(e)}")
#             return False

#     def archive_event(self, event_id: str) -> bool:
#         """Archive a dead letter event (mark as permanently failed)"""
#         try:
#             event = self.db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
#             if not event:
#                 return False
        
#             event.status = WebhookStatus.ARCHIVED
#             event.archived_at = datetime.utcnow()
        
#             self.db.commit()
        
#             logger.info(f"Archived dead letter event {event_id}")
#             return True
        
#         except Exception as e:
#             logger.error(f"Error archiving event {event_id}: {str(e)}")
#             return False