import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

# Configure Celery using settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django app configs
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'update-coin-details-cache': {
        'task': 'analytics.tasks.update_all_coin_details',
        'schedule': crontab(hour=0, minute=0),  # Run at midnight
    },
    # 'fetch-reddit-posts-every-15-minutes': {
    #     'task': 'analytics.tasks.fetch_reddit_posts',
    #     'schedule': crontab(minute='*/15'),  # Run every 15 minutes
    # },
}