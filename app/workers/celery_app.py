from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "stem_grad_assistant",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.worker.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'app.worker.tasks.scrape_university_faculty': {'queue': 'scraping'},
        'app.worker.tasks.monitor_social_media': {'queue': 'monitoring'},
        'app.worker.tasks.update_program_requirements': {'queue': 'updates'},
    }
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    'scrape-faculty-daily': {
        'task': 'app.worker.tasks.scrape_university_faculty',
        'schedule': 86400.0,  # Daily
    },
    'monitor-social-media': {
        'task': 'app.worker.tasks.monitor_social_media',
        'schedule': 21600.0,  # Every 6 hours
    },
    'update-program-requirements': {
        'task': 'app.worker.tasks.update_program_requirements',
        'schedule': 604800.0,  # Weekly
    },
}