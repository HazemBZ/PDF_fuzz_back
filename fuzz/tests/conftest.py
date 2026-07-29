from unittest.mock import patch

import pytest
from django.test import Client

from fuzz.search import Search


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def upload_id():
    return "success-001"


@pytest.fixture
def mock_search_delete():
    with patch.object(Search, "delete") as mock:
        yield mock


@pytest.fixture
def mock_file_manager_delete():
    with patch("fuzz.delete_service.FileManager.delete_path_recursively") as mock:
        yield mock
