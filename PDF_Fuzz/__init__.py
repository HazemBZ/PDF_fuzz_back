from fuzz.search import Search
from PDF_Fuzz.celery import app as celery_app
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.


if Search.es is None:
    Search.connect()

__all__ = ("celery_app",)
