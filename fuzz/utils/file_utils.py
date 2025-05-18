import os
import pathlib

from PDF_Fuzz.settings import IMAGES_DIR, UPLOADS_DIR

cm = classmethod


class FileManager:
    def __init__(self):
        pass

    @cm
    def get_uploaded_files(cls, pattern="*"):
        exclusion_list = [".gitkeep"]
        path = pathlib.Path(UPLOADS_DIR)

        # Options: file.relative_to(path), file.name
        paths = [
            file
            for file in path.rglob(pattern)
            if file.is_file() and file.name not in exclusion_list
        ]
        return paths

    @cm
    def get_images(cls, pattern="*"):
        exclusion_list = [".gitkeep"]

        path = pathlib.Path(IMAGES_DIR)

        paths = [
            file
            for file in path.rglob(pattern)
            if file.is_file() and file.name not in exclusion_list
        ]
        return paths

    @cm
    def delete_path_recursively(cls, path, root=True):
        exclusion_list = [".gitkeep"]
        if path is None:
            print("Empty directory ", path)
            return
        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        if (
            os.path.isfile(path)
            # or os.path.islink(path)
            and path.name not in exclusion_list
        ):
            os.remove(path)  # Delete the file or link
        elif os.path.isdir(path):
            # Delete all contents first
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                cls.delete_path_recursively(item_path, False)
            # Then delete the empty directory
            if not root:
                os.rmdir(path)
