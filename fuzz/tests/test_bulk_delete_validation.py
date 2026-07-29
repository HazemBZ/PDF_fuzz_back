import json

import pytest
from django.core.files.base import ContentFile

from chunkedUpload.models import ChunkedUpload, FileProcessing

DELETE_URL = "/api/fuzz/file/delete"


# ---------------------------------------------------------------------------
# Malformed input → 400
# ---------------------------------------------------------------------------


class TestMalformedInput:
    def test_non_object_json_root_string(self, client):
        """JSON root must be an object (string root → 400)."""
        resp = client.post(DELETE_URL, data='"string-root"', content_type="application/json")
        assert resp.status_code == 400
        data = json.loads(resp.content)
        assert "object" in data.get("error", "").lower()

    def test_non_object_json_root_array(self, client):
        """JSON root must be an object (array root → 400)."""
        resp = client.post(DELETE_URL, data='["array-root"]', content_type="application/json")
        assert resp.status_code == 400
        data = json.loads(resp.content)
        assert "object" in data.get("error", "").lower()

    def test_missing_upload_ids_field(self, client):
        resp = client.post(DELETE_URL, {"invalid": True}, content_type="application/json")
        assert resp.status_code == 400
        data = json.loads(resp.content)
        assert "error" in data

    def test_upload_ids_not_a_list(self, client):
        resp = client.post(DELETE_URL, {"upload_ids": "not-a-list"}, content_type="application/json")
        assert resp.status_code == 400

    def test_upload_ids_empty_list(self, client):
        resp = client.post(DELETE_URL, {"upload_ids": []}, content_type="application/json")
        assert resp.status_code == 400

    def test_upload_ids_contains_non_string(self, client):
        resp = client.post(
            DELETE_URL, {"upload_ids": ["abc", 123]}, content_type="application/json"
        )
        assert resp.status_code == 400

    def test_upload_ids_contains_empty_string(self, client):
        resp = client.post(
            DELETE_URL, {"upload_ids": ["abc", ""]}, content_type="application/json"
        )
        assert resp.status_code == 400

    def test_upload_ids_contains_duplicates(self, client):
        resp = client.post(
            DELETE_URL, {"upload_ids": ["dup", "dup"]}, content_type="application/json"
        )
        assert resp.status_code == 400

    def test_non_post_method_returns_405(self, client):
        resp = client.get(DELETE_URL, {"upload_ids": ["x"]})
        assert resp.status_code == 405

    def test_invalid_json_body(self, client):
        resp = client.post(DELETE_URL, data="not json", content_type="text/plain")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Missing uploads — idempotent per-ID missing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMissingUploads:
    def test_all_missing(self, client, mock_search_delete, mock_file_manager_delete):
        resp = client.post(
            DELETE_URL,
            {"upload_ids": ["no-such-1", "no-such-2"]},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)
        assert len(data["results"]) == 2
        assert {"upload_id": "no-such-1", "status": "missing"} in data["results"]
        assert {"upload_id": "no-such-2", "status": "missing"} in data["results"]
        mock_search_delete.assert_not_called()
        mock_file_manager_delete.assert_not_called()

    def test_mixed_missing_and_present(self, client, mock_search_delete, mock_file_manager_delete):
        ChunkedUpload.objects.create(
            upload_id="present-1",
            filename="exists.pdf",
            realname="exists.pdf",
            status=2,
        )
        resp = client.post(
            DELETE_URL,
            {"upload_ids": ["present-1", "no-such-1"]},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)
        results = {r["upload_id"]: r for r in data["results"]}
        assert results["present-1"]["status"] == "deleted"
        assert results["no-such-1"]["status"] == "missing"


# ---------------------------------------------------------------------------
# Active processing conflict — reject before any cleanup
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestActiveProcessingConflict:
    @pytest.fixture
    def queued_upload(self, tmp_path):
        uid = "conflict-queued"
        upload = ChunkedUpload.objects.create(
            upload_id=uid, filename="active.pdf", realname="active.pdf", status=2
        )
        upload.file.save("active.pdf", ContentFile(b"pdf"), save=True)
        FileProcessing.objects.create(
            upload=upload, status=FileProcessing.STATUS_QUEUED
        )
        return uid

    @pytest.fixture
    def processing_upload(self, tmp_path):
        uid = "conflict-processing"
        upload = ChunkedUpload.objects.create(
            upload_id=uid, filename="proc.pdf", realname="proc.pdf", status=2
        )
        upload.file.save("proc.pdf", ContentFile(b"pdf"), save=True)
        FileProcessing.objects.create(
            upload=upload, status=FileProcessing.STATUS_PROCESSING
        )
        return uid

    def test_queued_rejected_no_cleanup(
        self, client, mock_search_delete, mock_file_manager_delete, queued_upload
    ):
        resp = client.post(
            DELETE_URL,
            {"upload_ids": [queued_upload]},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)
        result = data["results"][0]
        assert result["upload_id"] == queued_upload
        assert result["status"] == "conflict"
        assert "queued" in result.get("error", "").lower() or "processing" in result.get("error", "").lower()
        mock_search_delete.assert_not_called()
        mock_file_manager_delete.assert_not_called()
        assert ChunkedUpload.objects.filter(upload_id=queued_upload).exists()

    def test_processing_rejected_no_cleanup(
        self, client, mock_search_delete, mock_file_manager_delete, processing_upload
    ):
        resp = client.post(
            DELETE_URL,
            {"upload_ids": [processing_upload]},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = json.loads(resp.content)
        result = data["results"][0]
        assert result["status"] == "conflict"
        mock_search_delete.assert_not_called()
        mock_file_manager_delete.assert_not_called()
        assert ChunkedUpload.objects.filter(upload_id=processing_upload).exists()

    def test_terminal_status_allows_delete(
        self, client, mock_search_delete, mock_file_manager_delete, tmp_path
    ):
        for label, status_code in (
            ("success", FileProcessing.STATUS_SUCCESS),
            ("failed", FileProcessing.STATUS_FAILED),
        ):
            uid = f"terminal-{label}"
            upload = ChunkedUpload.objects.create(
                upload_id=uid, filename=f"{label}.pdf", realname=f"{label}.pdf", status=2
            )
            upload.file.save(f"{label}.pdf", ContentFile(b"pdf"), save=True)
            FileProcessing.objects.create(upload=upload, status=status_code)

            resp = client.post(
                DELETE_URL, {"upload_ids": [uid]}, content_type="application/json"
            )
            data = json.loads(resp.content)
            assert data["results"][0]["status"] == "deleted", f"Failed for {label}"
            assert not ChunkedUpload.objects.filter(upload_id=uid).exists()
