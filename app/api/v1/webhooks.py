from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
import logging
from app.integrations.webhook import webhook_receiver, WebhookSource, WebhookSignatureError, WebhookTimestampError
from app.integrations.event_pipeline import event_processor
from app.tasks import celery as celery_app

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

@router.post("/webhooks/{service_name}")
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

    result = await event_processor.process_event(payload)
    if not result.success:
        logger.error(f"Event processing failed: {result.error_message}")
        raise HTTPException(status_code=500, detail=result.error_message)
    return {"status": "ok", "event_id": payload.event_id}


@router.get("/webhooks/health")
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