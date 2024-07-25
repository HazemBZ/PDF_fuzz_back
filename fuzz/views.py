import json
import pathlib

from django.http import FileResponse, JsonResponse
from PDF_Fuzz.settings import ASSETS_DIR, IMAGES_DIR

from fuzz.utils.file_utils import get_files_from_folder, get_pdf_files_paths_list
from fuzz.utils.pdf_utils import get_keyword_matches_page_numbers
from fuzz.utils.setup_utils import check_images_folder, check_processed_files

# TODO: Delegate this to an endpoint that unloads file processing to a task queue
check_images_folder(IMAGES_DIR)
check_processed_files(ASSETS_DIR)


# =========== API ================
def get_all_file_names(
    request,
):
    pdf_file_names = list(
        map(lambda x: {"name": x.name, "path": str(x)}, get_pdf_files_paths_list())
    )
    return JsonResponse(
        pdf_file_names,
        safe=False,
    )


def get_all_images_by_file_name(request, fileName):
    image_obj = {
        "file": fileName,
        "images": list(
            map(
                lambda p: f"{request.build_absolute_uri()}image/path/{'/'.join(p.parts[1:])}",
                get_files_from_folder(pathlib.Path(IMAGES_DIR, fileName)),
            )
        ),
    }
    return JsonResponse(image_obj)


def get_images_by_keyword(request):
    body = request.body
    if not body:  # check if json later
        return JsonResponse({"message": "please POST request in `JSON` format"})

    req = json.loads(body)

    matched_pages_images = []
    for file in req["files"]:
        keyword = req["keyword"]
        image_matches = get_keyword_matches_page_numbers(pathlib.Path(file), keyword)

        matched_pages_images.append(
            {
                "file": file,
                "keyword": keyword,
                "matchedImages": list(
                    map(
                        lambda x: f"{request.build_absolute_uri().split('image')[0]}image/path/{str(x).replace('images/','')}",
                        filter(
                            lambda path: int(path.name.split("_")[0]) in image_matches,
                            get_files_from_folder(
                                pathlib.Path(IMAGES_DIR, pathlib.Path(file).stem),
                                "jpg",
                            ),
                        ),
                    )
                ),
            }
        )

    return JsonResponse(matched_pages_images, safe=False)


def get_image_from_path(request, image_path):
    return FileResponse(open(pathlib.Path(IMAGES_DIR, image_path), "rb"))
