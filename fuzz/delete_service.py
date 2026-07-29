"""Payload validation and per-upload lifecycle cleanup for bulk deletion."""

import os
import pathlib

from elasticsearch import ApiError, TransportError
from PDF_Fuzz.settings import IMAGES_DIR

from fuzz.search import Search
from fuzz.utils.file_utils import FileManager
from chunkedUpload.models import ChunkedUpload, FileProcessing

from logging import getLogger

logger = getLogger(__name__)


def _find_image_stem(upload):
    """Derive PDF stem for image directory lookup.

    Uses realname first (set on completion), falls back to filename,
    then file storage name. Never assumes ``.path`` works (remote
    storage may not support it).
    """
    raw = upload.realname or upload.filename or str(upload.file.name)
    return pathlib.Path(raw).stem


def delete_single_upload(upload_id):
    """Delete one upload's artifacts in order: ES → images → storage+DB.

    Returns a per-ID result dict with ``upload_id`` and ``status``.
    On error returns ``status: "error"`` with an ``error`` message
    and does **not** proceed to the next step.
    """
    try:
        upload = ChunkedUpload.objects.get(upload_id=upload_id)
    except ChunkedUpload.DoesNotExist:
        return {"upload_id": upload_id, "status": "missing"}

    # Reject uploads with active background processing ---------------
    try:
        proc = upload.processing
        if proc.status in (
            FileProcessing.STATUS_QUEUED,
            FileProcessing.STATUS_PROCESSING,
        ):
            return {
                "upload_id": upload_id,
                "status": "conflict",
                "error": "Upload is currently queued or being processed",
            }
    except FileProcessing.DoesNotExist:
        pass

    images_dir = os.path.join(IMAGES_DIR, _find_image_stem(upload))

    # 1) Elasticsearch -----------------------------------------------
    try:
        Search.delete(
            body={"query": {"term": {"upload_id": upload_id}}},
            refresh=True,
            wait_for_completion=True,
        )
    except (ApiError, TransportError):
        logger.exception("Failed to delete ES documents for %s", upload_id)
        return {
            "upload_id": upload_id,
            "status": "error",
            "error": "Elasticsearch deletion failed",
        }

    # 2) Derived images ----------------------------------------------
    try:
        FileManager.delete_path_recursively(images_dir, keep_root=False)
    except OSError:
        logger.exception("Failed to delete images for %s", upload_id)
        return {
            "upload_id": upload_id,
            "status": "error",
            "error": "Image deletion failed",
        }

    # 3) Storage file + DB record ------------------------------------
    try:
        upload.delete(delete_file=True)
    except OSError:
        logger.exception("Failed to delete upload record for %s", upload_id)
        return {
            "upload_id": upload_id,
            "status": "error",
            "error": "Upload deletion failed",
        }

    return {"upload_id": upload_id, "status": "deleted"}


def validate_delete_payload(body):
    """Validate parsed request body for bulk delete.

    Returns ``(upload_ids, None)`` on success or
    ``(None, error_dict)`` on validation failure.
    """
    if not isinstance(body, dict):
        return None, {"error": "Request body must be a JSON object"}

    upload_ids = body.get("upload_ids")

    if not isinstance(upload_ids, list):
        return None, {"error": "upload_ids must be a non-empty array"}
    if len(upload_ids) == 0:
        return None, {"error": "upload_ids must not be empty"}
    if not all(isinstance(uid, str) and len(uid) > 0 for uid in upload_ids):
        return None, {"error": "Each upload_id must be a non-empty string"}
    if len(upload_ids) != len(set(upload_ids)):
        return None, {"error": "upload_ids must be unique"}

    return upload_ids, None


def delete_selected(upload_ids):
    """Execute deletion for every upload_id in the list.

    Returns a list of per-ID result dicts.
    """
    return [delete_single_upload(uid) for uid in upload_ids]
