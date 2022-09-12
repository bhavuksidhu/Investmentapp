import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'invest.settings')

app = Celery('invest',include=["api.tasks"])
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    "update_stock_prices": {
        "task": "api.tasks.update_stock_prices",
         "schedule": crontab(minute="*/20"),
    },
    "calculate_portfolio_value": {
    "task": "api.tasks.calculate_portfolio_value",
        "schedule": crontab(hour=1, minute=0),
    },
    "deactivate_subscriptions": {
        "task": "api.tasks.deactivate_subscriptions",
         "schedule": crontab(hour=2, minute=0),
    },
    "temp": {
        "task": "api.tasks.temp",
         "schedule":crontab(minute="*/1"),
    },
}

app.autodiscover_tasks()
