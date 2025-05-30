import logging
import os

from pdf2image import (
    convert_from_path,
)

logger = logging.getLogger(__name__)


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
