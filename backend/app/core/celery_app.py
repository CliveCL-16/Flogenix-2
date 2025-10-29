"""
Celery Configuration for Asynchronous Task Processing
Handles background processing of claims and agent workflows
"""

from celery import Celery
from celery.signals import after_setup_logger
from app.core.config import get_settings
import logging

# Get settings
settings = get_settings()

# Create Celery app
celery_app = Celery(
    "flogenix_enterprise",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
    include=[
        "app.tasks.claim_processing",
        "app.tasks.notification_tasks",
        "app.tasks.audit_tasks",
        "app.tasks.maintenance_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer=settings.celery.task_serializer,
    accept_content=settings.celery.accept_content,
    result_serializer=settings.celery.result_serializer,
    timezone=settings.celery.timezone,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    beat_schedule={
        # Periodic maintenance tasks
        'cleanup-expired-sessions': {
            'task': 'app.tasks.maintenance_tasks.cleanup_expired_sessions',
            'schedule': 300.0,  # Every 5 minutes
        },
        'update-system-metrics': {
            'task': 'app.tasks.maintenance_tasks.update_system_metrics',
            'schedule': 60.0,  # Every minute
        },
        'process-audit-logs': {
            'task': 'app.tasks.audit_tasks.process_audit_logs',
            'schedule': 600.0,  # Every 10 minutes
        },
    }
)

# Configure logging
@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if configured
    if settings.logging.file_path:
        file_handler = logging.FileHandler(settings.logging.file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

# Task routing
celery_app.conf.task_routes = {
    'app.tasks.claim_processing.*': {'queue': 'claims'},
    'app.tasks.notification_tasks.*': {'queue': 'notifications'},
    'app.tasks.audit_tasks.*': {'queue': 'audit'},
    'app.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
}

# Task priority
celery_app.conf.task_default_priority = 5
celery_app.conf.worker_disable_rate_limits = True

if __name__ == '__main__':
    celery_app.start()