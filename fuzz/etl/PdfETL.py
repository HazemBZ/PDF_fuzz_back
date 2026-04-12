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
        return list(self.iter_pages_text(file))

    def iter_pages_text(self, file):
        with pymupdf.open(file) as doc:
            for page in doc:
                text = page.get_text()
                sanitized_text = text.replace("\x00", "\ufffd")
                yield sanitized_text

    def transform_to_es_document(self, pages_text):
        return list(self.iter_es_documents(pages_text))

    def iter_es_documents(self, pages_text):
        filepath = self.file
        try:
            for i, text in enumerate(pages_text):
                yield {
                    "file_path": filepath.name,
                    "content": text,
                    "page_number": i + 1,
                    "page_id": i + 1,
                }
        except Exception:
            logger.exception("")
            return

    def transform_pages_to_render_images(self, file):
        """For each document page create render images"""
        images_list = convert_from_path(file)
        return images_list

    def iter_pages_to_render_images(self, file):
        with pymupdf.open(file) as doc:
            total_pages = doc.page_count

        for page_number in range(1, total_pages + 1):
            page_images = convert_from_path(
                file,
                first_page=page_number,
                last_page=page_number,
            )
            if not page_images:
                continue
            yield page_number, page_images[0]

    def load_es_documents(self, documents, batch_size=100):
        """Save document data to a vector db"""
        if documents is None:
            return

        buffer = []
        for document in documents:
            buffer.append(document)
            if len(buffer) >= batch_size:
                Search.insert_documents(self.es_index, buffer)
                buffer.clear()

        if buffer:
            Search.insert_documents(self.es_index, buffer)

    def load_image_files(self, image_files):
        file_path = self.file
        destination = IMAGES_DIR
        extension = "jpg"
        filename = file_path.stem

        if image_files is None:
            logger.debug(f"no images for {file_path}")
            return

        destination_dir = os.path.join(destination, filename)
        images_written = 0
        for c, image_item in enumerate(image_files, start=1):
            page_number = c
            image = image_item
            if isinstance(image_item, tuple) and len(image_item) == 2:
                page_number, image = image_item

            if images_written == 0:
                os.makedirs(destination_dir, exist_ok=True)

            image.save(
                os.path.join(destination_dir, f"{page_number}_{filename}.{extension}")
            )
            image.close()
            images_written += 1

        if images_written == 0:
            logger.debug(f"no images for {file_path}")
            return

        logger.info(f"finished saving images to {destination}")

    def execute(self):
        """Apply etl pipeline"""

        pages_text = self.iter_pages_text(self.file)
        es_documents = self.iter_es_documents(pages_text)
        self.load_es_documents(es_documents)

        image_files = self.iter_pages_to_render_images(self.file)
        self.load_image_files(image_files)
