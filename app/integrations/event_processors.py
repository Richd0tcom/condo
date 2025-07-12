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


