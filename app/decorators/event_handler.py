from functools import wraps
from typing import Callable, Any
import asyncio
import logging

import structlog
from app.core.event_pipeline import EventPipeline, event_emitter, processing_pipeline
from app.schemas.webhooks import ProcessingResult, WebhookPayload 

logger = structlog.get_logger(__name__)

def event_handler(event_type: str, pipeline: EventPipeline = None):
    """
    Decorator that wraps handlers with the full processing pipeline
    """
    def decorator(handler_func: Callable) -> Callable:
        @wraps(handler_func)
        async def wrapper(payload: WebhookPayload) -> ProcessingResult:
            current_pipeline = pipeline or processing_pipeline
            
            try:
                if await current_pipeline.is_duplicate_event(payload):
                    logger.info(f"Duplicate event detected: {payload.event_id}")
                    result = ProcessingResult(
                        success=True,
                        metadata={"skipped": "duplicate_event"}
                    )
                    await current_pipeline.mark_event_processed(payload, result)
                    return result
                
                processed_payload = await current_pipeline.apply_middleware(payload)
                
                logger.info(f"Processing event: {processed_payload.event_type} - {processed_payload.event_id}")
                result = await handler_func(processed_payload)
                
                await current_pipeline.mark_event_processed(payload, result)
                
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
                    await current_pipeline.mark_event_processed(payload, result)
                except Exception as mark_error:
                    logger.error(f"Error marking failed event: {mark_error}")
                
                return result
        
        # Register the wrapped handler with pymitter
        event_emitter.on(event_type, wrapper)
        logger.info(f"Registered handler for event: {event_type}")
        
        return wrapper
    
    return decorator