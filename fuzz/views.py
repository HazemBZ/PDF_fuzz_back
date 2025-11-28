import json
import os
import pathlib
from itertools import groupby

import magic
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from PDF_Fuzz.settings import IMAGES_DIR

from fuzz.search import Search
from fuzz.utils.file_utils import FileManager


def get_all_file_names(request):
    pdf_file_names = list(
        map(
            lambda x: {"name": x.name, "path": str(x)},
            FileManager.get_uploaded_files("*.pdf"),
        )
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
                FileManager.get_images(fileName),
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
        file_name = path.split("/")[-1].replace(".pdf", ".jpg")
        stripped_name = file_name.replace(".jpg", "")
        return f"{stripped_name}/{count}_{file_name}"

    res = Search.get_matching_keyword(keyword)["hits"]["hits"]

    formatted = []

    for key, items in groupby(res, lambda x: x["_source"]["file_path"]):
        match_group = {}

        match_group["file"] = key
        match_group["matchedImages"] = [
            build_image_name(key, item["_source"]["page_id"]) for item in items
        ]
        match_group["keyword"] = keyword
        formatted.append(match_group)

    return JsonResponse(formatted, safe=False)


def get_image_from_path(request, image_path):
    return FileResponse(open(pathlib.Path(IMAGES_DIR, image_path), "rb"))


@xframe_options_exempt
def read_file(request, document_name):
    file_path = FileManager.get_uploaded_files(f"*{document_name}")[0]

    content_type = magic.from_file(file_path, mime=True)

    with open(file_path, "rb") as file:
        file_data = file.read()

    response = HttpResponse(file_data, content_type=content_type)
    response["Content-Disposition"] = f"inline;filename={os.path.basename(file_path)}"

    return response
