from fuzz.etl.Orchestrator import ETLOrchestrator
from celery import shared_task

import logging

from pathlib import Path

logger = logging.getLogger(__name__)


@shared_task
def process_file(file):
    path = Path(file)
    logger.info(f"processing file {file}")
    ETLOrchestrator.process(path)
    return "ok"


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