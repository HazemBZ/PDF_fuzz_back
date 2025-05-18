from fuzz.etl.PdfETL import PdfETL
from fuzz.etl.ImageETL import ImageETL

import logging

logger = logging.getLogger(__name__)

cm = classmethod

class ETLOrchestrator:
    """Handles ETL execution according to extension rules"""

    def __init__(self):
        pass
    @cm
    def process(cls, file):
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
