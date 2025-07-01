from celery import Task
from app.tasks.celery import celery_app
from app.services.sync_engine import DataSyncEngine
from app.core.database import get_db
import logging
import asyncio

logger = logging.getLogger(__name__)

class SyncCallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Sync task {task_id} completed successfully")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Sync task {task_id} failed: {exc}")
        
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Sync task {task_id} retrying: {exc}")

@celery_app.task(bind=True, base=SyncCallbackTask, name="trigger_sync_task")
def trigger_sync_task(self, organization_id, service_name, entity_type=None, force=False):
    """Celery task to trigger a sync for a service/entity."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def run():
            async with get_db() as db:

                sync_engine = DataSyncEngine()
                result = await sync_engine.trigger_sync(
                    db=db,
                    organization_id=organization_id,
                    service_name=service_name,
                    entity_type=entity_type,
                    force=force
                )
                return result
        try:
            result = loop.run_until_complete(run())
        finally:
            loop.close()
        logger.info(f"Sync triggered for org={organization_id}, service={service_name}, entity={entity_type}")
        return result.__dict__
    except Exception as exc:
        logger.error(f"Error in trigger_sync_task: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries) if self.request.retries < self.max_retries else exc

@celery_app.task(bind=True, base=SyncCallbackTask, name="batch_sync_task")
def batch_sync_task(self, organization_id):
    """Celery task to batch sync all services for an organization."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def run():
            async with get_db() as db:
                sync_engine = DataSyncEngine()
                results = await sync_engine.batch_sync(
                    db=db,
                    organization_id=organization_id
                )
                return {k: v.__dict__ for k, v in results.items()}
        try:
            results = loop.run_until_complete(run())
        finally:
            loop.close()
        logger.info(f"Batch sync triggered for org={organization_id}")
        return results
    except Exception as exc:
        logger.error(f"Error in batch_sync_task: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries) if self.request.retries < self.max_retries else exc 