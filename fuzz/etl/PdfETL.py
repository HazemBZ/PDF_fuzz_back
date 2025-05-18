import logging
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from fuzz.search import Search
import os

from PDF_Fuzz.settings import IMAGES_DIR


from pdf2image import (
    convert_from_path,
)

logger = logging.getLogger(__name__)


class PdfETL:
    def __init__(self, file):
        self.file = file
        self.reader = "SET_READER"
        self.loader = "SET_LOADER"
        self.es_index = "pdf_contents_doc"

    def extract_page_text(self, page):
        """
        finds and returns all text containers in a Page
        """
        text = ""
        for el in page:
            if isinstance(el, LTTextContainer):
                text += el.get_text()
        return text

    def extract_pages(self, file):
        """
        -> (pages[], page_layouts[])
        pages: list of pages objects
        pages_layout (generator returns page objects)
        """
        pages_layout = []
        pages = []
        try:
            # pages generator
            pages_layout = extract_pages(file)
            while el := next(pages_layout):
                # save in pages list
                pages.append(el)
        except StopIteration:
            pass
        except Exception:
            logger.exception(f"Failed to completely process file '{file}'")
        finally:
            return pages, pages_layout

    def transform_to_es_document(self, pages):
        documents = []
        filepath = self.file
        try:
            for i, page in enumerate(pages):
                extracted_text = self.extract_page_text(page)
                documents.append(
                    {
                        "file_path": filepath.name,
                        "content": extracted_text,
                        "page_number": i + 1,
                        "page_id": page.pageid,
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
        # Search.
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
            # print(f"saving {c}_{file_path.stem}.{extension}")
            i.save(
                os.path.join(destination, filename, f"{c + 1}_{filename}.{extension}")
            )  # c+1 => pages start from 1
            logger.info(f"finished saving images to {destination}")

    # #NOW
    def execute(self):
        """Apply etl pipeline"""

        # Extract pages
        pages, _ = self.extract_pages(self.file)

        # Transform to es document
        es_documents = self.transform_to_es_document(pages)

        # Load es documents
        self.load_es_documents(es_documents)

        ## Extract images
        image_files = self.transform_pages_to_render_images()

        ## Save images
        self.load_image_files(image_files)
