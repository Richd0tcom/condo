from celery import Celery
from app.core.settings import settings
import os


celery_app = Celery(
    "saas_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.webhook_tasks",
    ]
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  
    task_soft_time_limit=25 * 60,  
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_default_retry_delay=60,  
    task_max_retries=3,
    task_routes={
        "app.tasks.webhook.*": {"queue": "webhooks"},
        'app.tasks.data_sync.*': {'queue': 'data_sync'},
        "app.tasks.*": {"queue": "default"},
        
    },
    # Dead letter queue configuration, TODO(Richdotcom)  revist this when doing external config
    task_reject_on_worker_lost=True,
    task_ignore_result=False,


    # Beat schedule for periodic tasks
    # beat_schedule={
    #     'check-integration-health': {
    #         'task': 'app.services.integration_health.check_integration_health',
    #         'schedule': 300.0,  
    #     },
    #     'cleanup-old-webhook-events': {
    #         'task': 'app.services.webhook_processor.cleanup_old_events',
    #         'schedule': 3600.0, 
    #     },
    #     'process-dead-letter-queue': {
    #         'task': 'app.services.webhook_processor.process_dead_letter_queue',
    #         'schedule': 1800.0, 
    #     },
    # },
)


@celery_app.task(bind=True)
def health_check(self):
    """Health check task for Celery workers"""
    return {"status": "healthy", "task_id": self.request.id}