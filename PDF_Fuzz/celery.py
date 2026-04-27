import logging
import os

from celery import Celery
from celery.signals import setup_logging

logger = logging.getLogger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PDF_Fuzz.settings")

# Import test helper after DJANGO_SETTINGS_MODULE is set to avoid
# AppRegistryNotReady errors during module import.
from fuzz.tasks import test_connection

app = Celery(
    "PDF_Fuzz", backend="redis://redis:6379/0", broker="amqp://guest@rabbitmq//"
)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Search.connect()

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


@setup_logging.connect
def config_loggers(*args, **kwags):
    from logging.config import dictConfig

    from django.conf import settings

    dictConfig(settings.CELERY_LOGGING)


if test_connection():
    logger.info("✅ Successfully connected to Celery worker!")
else:
    logger.warn("❌ Connection to Celery worker failed")
