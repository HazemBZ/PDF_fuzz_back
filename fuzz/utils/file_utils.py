import os
import pathlib

from PDF_Fuzz.settings import ASSETS_DIR


def get_pdf_files_paths_list(folder=ASSETS_DIR):
    pdf_files = []
    for root, _dir, files in os.walk(os.path.join(ASSETS_DIR)):
        pdf_files.extend(pathlib.Path(root).glob("*.pdf"))
    return pdf_files


def get_files_from_folder(folder, ext="pdf", filter_func=None):
    paths = []
    for root, _dir, files in os.walk(folder):
        paths.extend(pathlib.Path(root).glob(f"*.{ext}"))
    return list(paths)

