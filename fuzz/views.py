from django.utils._os import safe_join
from django.http import JsonResponse
from django.http import FileResponse
from django.conf import settings

from fuzz.utils.file_utils import get_pdf_files_paths_list, get_files_from_folder
from fuzz.utils.pdf_utils import (
    pdf_to_pages,
    find_pages_with_text,
    convert_pdf_to_images,
    save_images_to_dest,
    get_pdf_matched_pages_images,
    process_pdf_files_to_dest,
    get_keyword_matches_page_numbers,
)
from fuzz.utils.setup_utils import check_images_folder, check_processed_files
import os
import pathlib

KEYWORD = "Auto"
PDF_FOLDER = "PFE"
IMAGES_FOLDER = "images"

check_images_folder(IMAGES_FOLDER)
check_processed_files(PDF_FOLDER)


# =========== API ================

# @app.route("/file/names")
def get_all_file_names(request, ):
    pdf_file_names = list(map(lambda x: x.name, get_pdf_files_paths_list()))
    return JsonResponse(pdf_file_names, safe=False,)


# @app.route("/image/all/<string:fileName>")
def get_all_images_by_file_name(request, fileName):
    image_obj = {
        "file": fileName,
        "images": list(
            map(
                lambda p: f"{request.build_absolute_uri()}image/path/{'/'.join(p.parts[1:])}",
                get_files_from_folder(pathlib.Path(IMAGES_FOLDER, fileName)), # <--- FIXED
            )
        ),
    }
    # return jsonify(image_obj) # <-- FIXED
    return JsonResponse(image_obj)


# @app.route("/image/by/keyword", methods=["POST"])
def get_images_by_keyword(request, ):
    
    import json
    print(dir(request))
    print('--'*10)
    print(request.body)
    print('--'*10)

    print(json.loads(request.body))
    print(f"--------> ABSOLUTE {request.build_absolute_uri()}")
    body = request.body
    if not body: # check if json later
        return JsonResponse({
            'message': "please POST request in `JSON` format"
        })
    # req = request.get_json()
    req = json.loads(body)
    matched_pages_images = []
    for file in req["files"]:
        print("fi")
        keyword = req["keyword"]
        image_matches = get_keyword_matches_page_numbers(
            pathlib.Path(PDF_FOLDER, file), keyword
        )

        matched_pages_images.append(
            {
                "file": file,
                "keyword": keyword,
                "matchedImages": list(
                    map(
                        lambda x: f"{request.build_absolute_uri().split('image')[0]}image/path/{str(x).replace('images/','')}",
                        get_files_from_folder(
                            pathlib.Path(IMAGES_FOLDER, pathlib.Path(file).stem),
                            # pathlib.Path(file).stem,
                            fil_func=lambda x: int(x.name.split("_")[0])
                            in image_matches,
                        ),
                    )
                ),
            }
        )

    return JsonResponse(matched_pages_images, safe=False)


# @app.route("/image/path/<path:image_path>")
def get_image_from_path(request, image_path):
    # print("immage path => "+ str(image_path))
    # return flask.send_file(safe_join("images", image_path))
    print(f'receivef path{image_path}')
    return FileResponse(open(pathlib.Path("images", image_path), 'rb'))

### <---------  This block should not be here ---------->
# if __name__ == "__main__":
#     check_images_folder(IMAGES_FOLDER)
#     check_processed_files(PDF_FOLDER)
