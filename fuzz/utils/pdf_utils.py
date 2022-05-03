from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from pdf2image import (
    convert_from_path,
    # convert_from_bytes
)
import os


FILES_DIR = "PFE"
IMG_FOLDER = "images"

pages_struct = []

## : tuple(list_of_pages, generator_of_pages)


def pdf_to_pages(name):
    """
    returns pages (list of pages objects) and pages_layout (generator returns page objects)
    """
    pages_layout = []
    pages = []
    print(f"processing '{name}'")
    try:
        # pages generator
        pages_layout = extract_pages(name)
        while el := next(pages_layout):
            # save in pages list
            pages.append(el)
    except StopIteration:
        pass
    except Exception as e:
        print(f"Failed to completely process file '{name}'")
    # print(f"Layout ======= \n{pages_layout}")
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


# should be repurposed/scrapped !
## returns a list with struct that contains infor about pages with matching keywords
## returned struct: {file: file_name, pageIndex: page index inside the list, pageNumber; extracted page number, lookupText: used keyword, pageText: the extracted text from the page}
def find_pages_with_text(text, pages, lower=True):
    pages_with_text = []
    for i, page in enumerate(pages):
        extracted_text = extract_page_text(page)
        if text.lower() in extracted_text.lower():
            pages_with_text.append(
                {
                    "pageIndex": i,
                    "pageID": page.pageid,
                    "pageNumber": extracted_text[-2],
                    "lookupText": text,
                    "pageText": extracted_text,
                }
            )

    return pages_with_text


def get_keyword_matches_page_numbers(f_path, keyword):
    pages, _ = pdf_to_pages(f_path)
    pages_with_text = set()
    for i, page in enumerate(pages):
        extracted_text = extract_page_text(page)
        if keyword.lower() in extracted_text.lower():
            # pages_with_text.append({"pageIndex": i, "pageID": page.pageid, "pageNumber": extracted_text[-2], "lookupText": text, "pageText": extracted_text})
            pages_with_text.add(page.pageid)

    return list(pages_with_text)


def convert_pdf_to_images(path):
    """
    ()-> list of PIL images (currently can not select specific pages only batch conversion)
    """
    images_list = convert_from_path(path)
    return images_list


# should be scrapped !
def get_pdf_matched_pages_images(path, l=[]):
    if not l:
        print(f"no matched pages {l}")
        return
    else:
        print(f"converting images of {path} for matched pages{l}")
    images_list = convert_from_path(path)
    print(f"images converion {images_list}")
    return [images_list[i - 1] for i in l]


def save_images_to_dest(dest, file_path, images, extension="jpg"):
    if not images:
        print(f"no images for {file_path}")
        return
    os.system(f"mkdir '{dest}'")
    for c, i in enumerate(images):
        # print(f"saving {c}_{file_path.stem}.{extension}")
        i.save(
            os.path.join(dest, f"{c+1}_{file_path.stem}.{extension}")
        )  # c+1 => pages start from 1
    print(f"finished saving images {dest}")


def process_pdf_files_to_dest(r_dest, f_paths_list):
    if not f_paths_list:
        print("no files to process")
        return
    else:
        for fp in f_paths_list:
            saving_folder = os.path.join(r_dest, fp.stem)
            images_list = convert_from_path(fp)

            save_images_to_dest(saving_folder, fp, images_list)
