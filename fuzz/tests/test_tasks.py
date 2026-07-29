from unittest.mock import patch

import pytest

from fuzz.tasks import process_file


def test_process_file_rejects_missing_input_with_absolute_path(tmp_path):
    missing_file = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError, match=str(missing_file)):
        process_file.run(str(missing_file))


def test_process_file_passes_resolved_input_to_etl(tmp_path):
    pdf_file = tmp_path / "document.pdf"
    pdf_file.write_bytes(b"pdf")

    with patch("fuzz.tasks.ETLOrchestrator.process") as process:
        assert process_file.run(str(pdf_file)) == "ok"

    process.assert_called_once_with(pdf_file, None)
