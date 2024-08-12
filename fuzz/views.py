import json
import pathlib

from django.http import FileResponse, JsonResponse
from PDF_Fuzz.settings import IMAGES_DIR

from fuzz.utils.file_utils import get_files_from_folder, get_pdf_files_paths_list
from fuzz.search import Search
from itertools import groupby

# TODO: Delegate this to an endpoint that unloads file processing to a task queue
# check_images_folder(IMAGES_DIR)
# check_processed_files(ASSETS_DIR)


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
    keyword = req["keyword"]
    
    def build_image_name(path, count):
        file_name = path.split('/')[-1].replace('.pdf', '.jpg')
        stripped_name = file_name.replace('.jpg', '')
        return f"{stripped_name}/{count}_{file_name}"
        
    res = Search.get_matching_keyword(keyword)['hits']['hits']
    
    formatted = []
    
    for key, items in groupby(res, lambda x: x['_source']['file_path']):
        match_group = {}
        
        match_group['file'] = key
        match_group['matchedImages'] = [build_image_name(key, item['_source']['page_id']) for item in items ]
        match_group['keyword'] = keyword
        formatted.append(match_group)

    return JsonResponse(formatted, safe=False)


def get_image_from_path(request, image_path):
    return FileResponse(open(pathlib.Path(IMAGES_DIR, image_path), "rb"))
