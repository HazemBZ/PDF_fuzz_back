from fuzz.utils.file_utils import get_pdf_files_paths_list
from fuzz.utils.pdf_utils import process_pdf_files_to_dest
from PDF_Fuzz.settings import ASSETS_DIR, IMAGES_DIR
import os


KEYWORD = "Auto"

def check_images_folder(folder):
    if not os.access(IMAGES_DIR, os.R_OK):
        os.system(f"mkdir '{IMAGES_DIR}'")
        os.system(f"touch '{IMAGES_DIR}/.gitkeep'")


def check_processed_files(folder):
    _file_list = get_pdf_files_paths_list(ASSETS_DIR)
    for f in _file_list:
        if not os.access(os.path.join(IMAGES_DIR, f.stem), os.R_OK):
            print(f"processing '{f}'")
            process_pdf_files_to_dest(IMAGES_DIR, [f])
            print(20 * "-")
