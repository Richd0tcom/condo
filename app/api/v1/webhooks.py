from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
import logging

import structlog
from app.core.event_pipeline import event_emitter
from app.integrations.webhook import webhook_receiver, WebhookSource, WebhookSignatureError, WebhookTimestampError
from app.tasks import celery as celery_app

router = APIRouter()
security = HTTPBearer()
logger = structlog.get_logger(__name__)

@router.post("/{service_name}")
async def receive_webhook(
    service_name: str,
    request: Request
):
    """
    Receive webhook from external services
    This endpoint handles webhooks from multiple external services
    """
    try:
        source = WebhookSource(service_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Unknown webhook source")

    headers = request.headers
    config = webhook_receiver.configs.get(source)
    if not config:
        raise HTTPException(status_code=400, detail=f"No config for webhook source: {service_name}")
    signature = headers.get(config.signature_header)
    timestamp = headers.get(config.timestamp_header)

    try:
        
        payload = await webhook_receiver.process_webhook(
            request=request,
            source=source,
            signature=signature,
            timestamp=timestamp
        )
    except (WebhookSignatureError, WebhookTimestampError) as e:
        logger.warning(f"Webhook validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    event_emitter.emit_future(payload.event_type, payload)

    return {"status": "ok", "event_id": payload.event_id}


@router.get("/health")
async def webhook_health_check():
    """Health check endpoint for webhook processing system"""
    
    try:
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        if not active_workers:
            return {
                "status": "unhealthy",
                "message": "No active Celery workers found",
                "workers": 0
            }
        total_workers = len(active_workers)
        return {
            "status": "healthy",
            "message": "Webhook processing system is operational",
            "workers": total_workers,
            "worker_details": active_workers
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "workers": 0
        }