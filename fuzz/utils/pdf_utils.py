import logging
import os

from pdf2image import (
    convert_from_path,
)
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

logger = logging.getLogger(__name__)


def pdf_to_pages(name):
    """
    -> (pages[], page_layouts[])
    pages: list of pages objects
    pages_layout (generator returns page objects)
    """
    pages_layout = []
    pages = []
    try:
        # pages generator
        pages_layout = extract_pages(name)
        while el := next(pages_layout):
            # save in pages list
            pages.append(el)
    except StopIteration:
        pass
    except Exception:
        logger.exception(f"Failed to completely process file '{name}'")
    finally:
        return pages, pages_layout


def extract_page_text(page):
    """
    finds and returns all text containers in a Page
    """
    text = ""
    for el in page:
        if isinstance(el, LTTextContainer):
            text += el.get_text()
    return text


def get_file_documents(f_path):
    """
    Transforms pdf pages into document format to be ingested by es
    """
    try:
        pages, _ = pdf_to_pages(f_path)
        documents = []
        for i, page in enumerate(pages):
            extracted_text = extract_page_text(page)
            documents.append(
                {
                    "file_path": str(f_path),
                    "content": extracted_text,
                    "page_number": i + 1,
                    "page_id": page.pageid,
                }
            )
        return documents
    except Exception:
        logger.exception("")
        return []


def convert_pdf_to_images(path):
    """
    Converts a pdf file to a list of PIL images (currently can not select specific pages only batch conversion)
    -> List[Image]
    """
    images_list = convert_from_path(path)
    return images_list


def save_images_to_dest(dest, file_path, images, extension="jpg"):
    if not images:
        logger.debug(f"no images for {file_path}")
        return
    os.makedirs(dest)
    for c, i in enumerate(images):
        # print(f"saving {c}_{file_path.stem}.{extension}")
        i.save(
            os.path.join(dest, f"{c + 1}_{file_path.stem}.{extension}")
        )  # c+1 => pages start from 1
    logger.info(f"finished saving images to {dest}")


def process_pdf_files_to_dest(r_dest, f_paths_list):
    """
    Takes a list of pdf filepaths then converts and saves them to a dest folder
    """
    if not f_paths_list:
        logger.info("no files to process")
        return
    else:
        for fp in f_paths_list:
            saving_folder = os.path.join(r_dest, fp.stem)
            images_list = convert_from_path(fp)
            save_images_to_dest(saving_folder, fp, images_list)
