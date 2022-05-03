from fuzz.utils.file_utils import get_pdf_files_paths_list
from fuzz.utils.pdf_utils import process_pdf_files_to_dest
import os


KEYWORD = "Auto"
PDF_FOLDER = "PFE"
IMAGES_FOLDER = "images"


def check_images_folder(folder):
    if not os.access(IMAGES_FOLDER, os.R_OK):
        os.system(f"mkdir '{IMAGES_FOLDER}'")
        os.system(f"touch '{IMAGES_FOLDER}/.gitkeep'")


def check_processed_files(folder):
    _file_list = get_pdf_files_paths_list(PDF_FOLDER)
    for f in _file_list:
        if not os.access(os.path.join(IMAGES_FOLDER, f.stem), os.R_OK):
            print(f"processing '{f}'")
            process_pdf_files_to_dest(IMAGES_FOLDER, [f])
            print(20 * "-")
