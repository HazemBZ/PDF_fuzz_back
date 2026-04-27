import logging
from pathlib import Path

from celery import current_task, shared_task
from django.apps import apps
from django.utils import timezone

from fuzz.etl.Orchestrator import ETLOrchestrator

logger = logging.getLogger(__name__)


@shared_task
def process_file(file, upload_id=None):
    path = Path(file)
    logger.info(f"processing file {file} upload_id={upload_id}")

    proc = None
    if upload_id:
        try:
            FileProcessing = apps.get_model("chunkedUpload", "FileProcessing")
            proc = FileProcessing.objects.get(upload__upload_id=upload_id)
            proc.status = FileProcessing.STATUS_PROCESSING
            proc.started_on = timezone.now()
            # current task id if available
            try:
                proc.task_id = current_task.request.id
            except Exception:
                pass
            proc.save()
        except Exception:
            # If model or record is not available yet, continue without processing updates
            proc = None

    try:
        ETLOrchestrator.process(path, upload_id)
        if proc:
            proc.status = FileProcessing.STATUS_SUCCESS
            proc.progress = 100
            proc.finished_on = timezone.now()
            proc.save()
        return "ok"
    except Exception as e:
        logger.exception("Error during ETL processing")
        if proc:
            proc.status = FileProcessing.STATUS_FAILED
            proc.error = str(e)
            proc.finished_on = timezone.now()
            proc.save()
        raise


@shared_task
def ping():
    return "pong"


# Test connection
def test_connection():
    result = ping.delay()
    try:
        # Wait for response with timeout
        return result.get(timeout=5) == "pong"
    except Exception:
        logger.exception("Connection failed")
        return False
