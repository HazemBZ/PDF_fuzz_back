from pathlib import Path

import pytest
from fuzz.etl.PdfETL import PdfETL
from fuzz.search import Search
from fuzz.utils.file_utils import FileManager
from PDF_Fuzz.settings import IMAGES_DIR


@pytest.fixture
def es_manager():
    yield Search
    Search.delete(body={"query": {"match": {"file_path": "lorem_ipsum.pdf"}}})


@pytest.fixture
def file():
    return Path("assets/data/lorem_ipsum.pdf")


@pytest.fixture
def file_manager():
    yield FileManager
    FileManager.delete_path_recursively(f"{IMAGES_DIR}/lorem_ipsum", keep_root=False)


@pytest.fixture
def etl(file):
    return PdfETL(file)


def test_extract_pages_text(file, etl):
    extracted_text = "".join(etl.extract_pages_text(file))
    assert (
        extracted_text
        == """Lorem ipsum dolor sit amet.\nMaecenas mi mauris, euismod vitae velit a.\nlorem ipsum\n"""
    )


## Test correct formatting
def test_transform_to_es_document(file, etl):
    pages_text = etl.extract_pages_text(file)
    es_documents = etl.transform_to_es_document(pages_text)
    assert es_documents == [
        {
            "file_path": file.name,
            "content": "Lorem ipsum dolor sit amet.\nMaecenas mi mauris, euismod vitae velit a.\nlorem ipsum\n",
            "page_number": 1,
            "page_id": 1,
        },
    ]


## Test returned images from pdf
def test_transform_pages_to_render_images(file, etl):
    images_list = etl.transform_pages_to_render_images(file)
    assert len(images_list) == 1


## Test es documents are being saved
def test_load_es_documents(file, etl, es_manager):
    pages_text = etl.extract_pages_text(file)
    es_documents = etl.transform_to_es_document(pages_text)
    etl.load_es_documents(es_documents)
    res = es_manager.search(
        fields=["file_path", "page_id", "page_number"],
        query={"match": {"file_path": "lorem_ipsum.pdf"}},
    )

    hits_number = res["hits"]["total"]["value"]

    assert hits_number == 1


## Test images are correctly saved
def test_load_image_files(file, etl, file_manager):
    image_files = etl.transform_pages_to_render_images(file)
    etl.load_image_files(image_files)
    images = file_manager.get_images("lorem_ipsum/*")

    assert len(images) == 1
