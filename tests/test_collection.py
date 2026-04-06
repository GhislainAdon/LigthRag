# tests/sdk/test_collection.py
import pytest
from unittest.mock import MagicMock
from pageindex.collection import Collection


@pytest.fixture
def col():
    backend = MagicMock()
    backend.list_documents.return_value = [
        {"doc_id": "d1", "doc_name": "paper.pdf", "doc_type": "pdf"}
    ]
    backend.get_document.return_value = {"doc_id": "d1", "doc_name": "paper.pdf"}
    backend.add_document.return_value = "d1"
    return Collection(name="papers", backend=backend)


def test_add(col):
    doc_id = col.add("paper.pdf")
    assert doc_id == "d1"
    col._backend.add_document.assert_called_once_with("papers", "paper.pdf")


def test_list_documents(col):
    docs = col.list_documents()
    assert len(docs) == 1
    assert docs[0]["doc_id"] == "d1"


def test_get_document(col):
    doc = col.get_document("d1")
    assert doc["doc_name"] == "paper.pdf"


def test_delete_document(col):
    col.delete_document("d1")
    col._backend.delete_document.assert_called_once_with("papers", "d1")


def test_name_property(col):
    assert col.name == "papers"
