import json
import os
import pathlib
from itertools import groupby

import magic
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from PDF_Fuzz.settings import IMAGES_DIR

from fuzz.delete_service import delete_selected, validate_delete_payload
from fuzz.search import Search
from fuzz.utils.file_utils import FileManager
from chunkedUpload.models import ChunkedUpload, FileProcessing

from logging import getLogger

logger = getLogger(__name__)


def delete_selected_files(request):
    """Bulk-delete uploaded PDFs by immutable ``upload_id``.

    Delegates payload validation and per-ID lifecycle cleanup to
    ``delete_service``.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    upload_ids, err = validate_delete_payload(body)
    if err is not None:
        return JsonResponse(err, status=400)

    results = delete_selected(upload_ids)
    return JsonResponse({"results": results})


def get_all_file_names(request):
    pdf_file_names = []

    # Iterate over ChunkedUpload records for PDF files instead of scanning filesystem
    uploads = ChunkedUpload.objects.filter(realname__iendswith='.pdf')

    for cu in uploads:
        try:
            logger.info(f"Checking ChunkedUpload {cu.upload_id} ({cu.filename})")
            name = cu.realname
            # .replace('.pdf', '')
            status_label = 'untracked'
            progress = None

            try:
                proc = cu.processing
                status_label = dict(FileProcessing.STATUS_CHOICES).get(proc.status, 'unknown')
                progress = proc.progress
            except FileProcessing.DoesNotExist:
                logger.info(f"ChunkedUpload {cu.upload_id} has no FileProcessing record")
                status_label = 'queued_or_not_started'

            # Use the file field path for the filesystem path (may raise if storage doesn't support it)
            file_path = None
            try:
                file_path = cu.file.path
            except Exception:
                # Fallback to the storage name/url if .path is not available
                file_path = str(cu.file.name)

            pdf_file_names.append({
                'id': cu.upload_id,
                'name': name,
                'path': file_path,
                'status': status_label,
                'progress': progress,
            })
        except Exception:
            logger.exception(f"Error checking ChunkedUpload {getattr(cu, 'upload_id', '<unknown>')}")
            pdf_file_names.append({
                'id': getattr(cu, 'upload_id', None),
                'name': getattr(cu, 'realname', '').replace('.pdf', ''),
                'path': getattr(cu.file, 'name', ''),
                'status': 'unknown',
                'progress': None,
            })

    return JsonResponse(pdf_file_names, safe=False)


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
    
    
    # TODO: Get upload_id from search result and add to response

    for key, items in groupby(res, lambda x: x["_source"]["file_path"]):
        match_group = {}
        
        upload_id = None

        match_group["file"] = key
        match_group["matchedImages"] = [
         
        ]
        for item in items:
            match_group["matchedImages"].append(build_image_name(key, item["_source"]["page_id"]))
            upload_id = item["_source"].get("upload_id")  # Assuming all items in the group have the same upload_id
        match_group["upload_id"] = upload_id  # Assuming all items in the group have the same upload_id
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
