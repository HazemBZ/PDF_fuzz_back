import logging
import os

from fuzz.search import Search
from pdf2image import (
    convert_from_path,
)
from PDF_Fuzz.settings import IMAGES_DIR
import pymupdf

logger = logging.getLogger(__name__)


class PdfETL:
    def __init__(self, file):
        self.file = file
        self.reader = "SET_READER"
        self.loader = "SET_LOADER"
        self.es_index = "pdf_contents_doc"

    def extract_pages_text(self, file):
        doc = pymupdf.open(file)
        pages_text = []
        for page in doc:
            text = page.get_text()
            # .encode("utf8")
            # Write page delimeter ??
            sanitized_text = text.replace("\x00", "\ufffd")
            pages_text.append(sanitized_text)

        doc.close()

        return pages_text

    def transform_to_es_document(self, pages_text):
        documents = []
        filepath = self.file
        try:
            for i, text in enumerate(pages_text):
                documents.append(
                    {
                        "file_path": filepath.name,
                        "content": text,
                        "page_number": i + 1,
                        "page_id": i + 1,
                    }
                )
            return documents
        except Exception:
            logger.exception("")
            return []

    def transform_pages_to_render_images(self):
        """For each document page create render images"""
        images_list = convert_from_path(self.file)
        return images_list

    def load_es_documents(self, documents):
        """Save document data to a vector db"""
        Search.insert_documents(self.es_index, documents)

    def load_image_files(self, image_files):
        file_path = self.file
        destination = IMAGES_DIR
        extension = "jpg"
        filename = file_path.stem

        if not image_files:
            logger.debug(f"no images for {file_path}")
            return
        os.makedirs(os.path.join(destination, filename))
        for c, i in enumerate(image_files):
            i.save(
                os.path.join(destination, filename, f"{c + 1}_{filename}.{extension}")
            )
            logger.info(f"finished saving images to {destination}")

    def execute(self):
        """Apply etl pipeline"""

        # Extract pages
        pages_text = self.extract_pages_text(self.file)

        # Transform to es document
        es_documents = self.transform_to_es_document(pages_text)

        # Load es documents
        self.load_es_documents(es_documents)

        # Extract images
        image_files = self.transform_pages_to_render_images()

        # Save images
        self.load_image_files(image_files)
