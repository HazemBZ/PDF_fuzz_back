import logging

from fuzz.etl.ImageETL import ImageETL
from fuzz.etl.PdfETL import PdfETL
from fuzz.search import Search


logger = logging.getLogger(__name__)

cm = classmethod


class ETLOrchestrator:
    """Handles ETL execution according to extension rules"""

    def __init__(self):
        pass

    @cm
    def startup(cls):
        if Search.es is None:
            Search.connect()

    @cm
    def process(cls, file):
        cls.startup()
        extension = file.suffix[1:]

        match extension:
            case "pdf":
                PdfETL(file).execute()
            case "png" | "jpg":
                ImageETL(file).execute()
            case item if item in ["doc", "docx"]:
                logger.warn(f"No executors yet for {file.name}")
            case _:
                pass
