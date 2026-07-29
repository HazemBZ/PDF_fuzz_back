import json
from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile

from elasticsearch import TransportError

from chunkedUpload.models import ChunkedUpload
from fuzz.search import Search
from PDF_Fuzz.settings import IMAGES_DIR

DELETE_URL = "/api/fuzz/file/delete"


# ---------------------------------------------------------------------------
# Terminal upload success — verify ordering and artifact cleanup
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTerminalUploadDelete:
    def test_success_cleans_es_images_and_storage_in_order(
        self, client, mock_search_delete, mock_file_manager_delete, tmp_path, upload_id
    ):
        upload = ChunkedUpload.objects.create(
            upload_id=upload_id,
            filename="report.pdf",
            realname="report.pdf",
            status=2,
        )
        upload.file.save("report.pdf", ContentFile(b"pdf-content"), save=True)

        resp = client.post(
            DELETE_URL,
            {"upload_ids": [upload_id]},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["results"] == [{"upload_id": upload_id, "status": "deleted"}]

        # ES delete_by_query with term filter + refresh + wait_for_completion
        mock_search_delete.assert_called_once_with(
            body={"query": {"term": {"upload_id": upload_id}}},
            refresh=True,
            wait_for_completion=True,
        )

        # Image dir cleanup called with correct stem
        mock_file_manager_delete.assert_called_once()
        call_args, call_kwargs = mock_file_manager_delete.call_args
        images_path = call_args[0]
        assert "report" in str(images_path)
        assert call_kwargs.get("keep_root") is False

        # DB record removed
        assert not ChunkedUpload.objects.filter(upload_id=upload_id).exists()

    def test_success_without_processing_record(
        self, client, mock_search_delete, mock_file_manager_delete, tmp_path
    ):
        uid = "no-proc-001"
        upload = ChunkedUpload.objects.create(
            upload_id=uid, filename="simple.pdf", realname="simple.pdf", status=2
        )
        upload.file.save("simple.pdf", ContentFile(b"pdf"), save=True)

        resp = client.post(DELETE_URL, {"upload_ids": [uid]}, content_type="application/json")
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert data["results"] == [{"upload_id": uid, "status": "deleted"}]
        mock_search_delete.assert_called_once()

    def test_stem_from_realname_fallback_to_filename(
        self, client, mock_search_delete, mock_file_manager_delete, tmp_path
    ):
        uid = "fallback-001"
        upload = ChunkedUpload.objects.create(
            upload_id=uid, filename="mydoc.pdf", realname="", status=2
        )
        upload.file.save("mydoc.pdf", ContentFile(b"pdf"), save=True)

        resp = client.post(DELETE_URL, {"upload_ids": [uid]}, content_type="application/json")
        assert resp.status_code == 200

        call_args, _ = mock_file_manager_delete.call_args
        images_path = str(call_args[0])
        assert "mydoc" in images_path or str(IMAGES_DIR) in images_path
        mock_search_delete.assert_called_once()


# ---------------------------------------------------------------------------
# Partial failures — per-ID error stops further cleanup for that ID
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPartialFailure:
    def test_es_failure_returns_error_and_skips_image_and_storage_cleanup(
        self, client, mock_file_manager_delete, tmp_path
    ):
        uid = "es-fail"
        upload = ChunkedUpload.objects.create(
            upload_id=uid, filename="esfail.pdf", realname="esfail.pdf", status=2
        )
        upload.file.save("esfail.pdf", ContentFile(b"pdf"), save=True)

        with patch.object(Search, "delete", side_effect=TransportError("ES timeout")):
            resp = client.post(
                DELETE_URL,
                {"upload_ids": [uid]},
                content_type="application/json",
            )

        assert resp.status_code == 200
        data = json.loads(resp.content)
        result = data["results"][0]
        assert result["status"] == "error"
        assert "Elasticsearch deletion failed" in result.get("error", "")
        mock_file_manager_delete.assert_not_called()
        assert ChunkedUpload.objects.filter(upload_id=uid).exists()

    def test_image_failure_skips_storage_cleanup(
        self, client, mock_search_delete, mock_file_manager_delete, tmp_path
    ):
        uid = "img-fail"
        upload = ChunkedUpload.objects.create(
            upload_id=uid, filename="imgfail.pdf", realname="imgfail.pdf", status=2
        )
        upload.file.save("imgfail.pdf", ContentFile(b"pdf"), save=True)

        mock_file_manager_delete.side_effect = OSError("Permission denied")

        resp = client.post(
            DELETE_URL,
            {"upload_ids": [uid]},
            content_type="application/json",
        )

        assert resp.status_code == 200
        data = json.loads(resp.content)
        result = data["results"][0]
        assert result["status"] == "error"
        assert "Image deletion failed" in result.get("error", "")
        mock_search_delete.assert_called_once()
        assert ChunkedUpload.objects.filter(upload_id=uid).exists()

    def test_independent_errors_dont_block_other_ids(
        self, client, mock_search_delete, mock_file_manager_delete, tmp_path
    ):
        good_uid = "good-001"
        bad_uid = "bad-001"

        for uid in (good_uid, bad_uid):
            upload = ChunkedUpload.objects.create(
                upload_id=uid,
                filename=f"{uid}.pdf",
                realname=f"{uid}.pdf",
                status=2,
            )
            upload.file.save(f"{uid}.pdf", ContentFile(b"pdf"), save=True)

        original_delete = Search.delete

        def side_effect(**kwargs):
            body = kwargs.get("body", {})
            term = body.get("query", {}).get("term", {})
            if term.get("upload_id") == bad_uid:
                raise TransportError("ES timeout")
            return original_delete(**kwargs)

        with patch.object(Search, "delete", side_effect=side_effect):
            resp = client.post(
                DELETE_URL,
                {"upload_ids": [good_uid, bad_uid]},
                content_type="application/json",
            )

        assert resp.status_code == 200
        data = json.loads(resp.content)
        results = {r["upload_id"]: r for r in data["results"]}
        assert results[good_uid]["status"] == "deleted"
        assert results[bad_uid]["status"] == "error"
        assert not ChunkedUpload.objects.filter(upload_id=good_uid).exists()
        assert ChunkedUpload.objects.filter(upload_id=bad_uid).exists()
