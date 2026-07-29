from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from chunkedUpload.views import ChunkedUploadCompleteView


def test_completion_preserves_storage_path_and_queues_absolute_file(tmp_path):
    upload_id = "upload-123"
    source = tmp_path / "uploads" / "chunked_uploads" / "upload.part"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"pdf")
    storage_name = "uploads/chunked_uploads/upload.part"
    file_field = SimpleNamespace(name=storage_name, path=str(source))
    instance = SimpleNamespace(
        file=file_field,
        realname="document.pdf",
        upload_id=upload_id,
        save=MagicMock(),
    )
    request = SimpleNamespace(POST={"upload_id": upload_id, "realname": "document.pdf"})
    async_result = SimpleNamespace(id="task-123")

    with (
        patch("chunkedUpload.views.ChunkedUpload.objects.get", return_value=instance),
        patch(
            "chunkedUpload.views.process_file.apply_async",
            return_value=async_result,
        ) as apply_async,
        patch("chunkedUpload.views.FileProcessing.objects.update_or_create"),
    ):
        ChunkedUploadCompleteView().on_completion(None, request)

    destination = source.with_name("document.pdf")
    assert destination.read_bytes() == b"pdf"
    assert not source.exists()
    assert file_field.name == str(Path(storage_name).with_name("document.pdf"))
    apply_async.assert_called_once_with(args=[str(destination), upload_id])
