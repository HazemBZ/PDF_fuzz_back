import logging
from django.core.management.base import BaseCommand
from fuzz.utils.file_utils import FileManager
from PDF_Fuzz.settings import IMAGES_DIR, UPLOADS_DIR
from chunkedUpload.models import ChunkedUpload
from fuzz.search import Search

logger = logging.getLogger(__name__)


# TODO: Cleanup es document index
class Command(BaseCommand):
    help = "Cleanup uploads related data"

    def add_arguments(self, *args, **kwargs):
        pass

    def handle(self, *args, **options):
        try:
            FileManager.delete_path_recursively(UPLOADS_DIR)
            FileManager.delete_path_recursively(IMAGES_DIR)
            ChunkedUpload.objects.all().delete()
            Search.create_index()

        except Exception:
            logger.exception("Failed to cleanup")
        else:
            self.stdout.write(self.style.SUCCESS("Data cleaned"))
