import pathlib


def get_files_from_folder(folder, ext="", fil_func=None):
    paths = pathlib.Path(".").glob(f"{folder}/*{'.'+ext if ext else ''}")
    if fil_func:
        paths = filter(fil_func, paths)
    return list(paths)


def get_pdf_files_paths_list(folder="PFE"):
    return get_files_from_folder(folder, "pdf")
