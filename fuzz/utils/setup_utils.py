import os
from timeit import default_timer as timer

from PDF_Fuzz.settings import ASSETS_DIR, IMAGES_DIR

from fuzz.utils.file_utils import get_pdf_files_paths_list
from fuzz.utils.pdf_utils import process_pdf_files_to_dest


def check_images_folder(folder):
    if not os.access(IMAGES_DIR, os.R_OK):
        os.makedirs(IMAGES_DIR)
        gitkeep = os.path.join(IMAGES_DIR, ".gitkeep")
        with open(gitkeep, "x"):
            pass


def check_processed_files(folder):
    _file_list = get_pdf_files_paths_list(ASSETS_DIR)
    for f in _file_list:
        if not os.access(os.path.join(IMAGES_DIR, f.stem), os.R_OK):
            print(f"processing '{f}'")
            start = timer()
            process_pdf_files_to_dest(IMAGES_DIR, [f])
            end = timer()
            print(f"Took: {end - start}")
            print(20 * "-")
