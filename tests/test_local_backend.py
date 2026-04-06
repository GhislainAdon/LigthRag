# tests/sdk/test_local_backend.py
import pytest
from pathlib import Path
from pageindex.backend.local import LocalBackend
from pageindex.storage.sqlite import SQLiteStorage
from pageindex.errors import FileTypeError


@pytest.fixture
def backend(tmp_path):
    storage = SQLiteStorage(str(tmp_path / "test.db"))
    files_dir = tmp_path / "files"
    return LocalBackend(storage=storage, files_dir=str(files_dir), model="gpt-4o")


def test_collection_lifecycle(backend):
    backend.get_or_create_collection("papers")
    assert "papers" in backend.list_collections()
    backend.delete_collection("papers")
    assert "papers" not in backend.list_collections()


def test_list_documents_empty(backend):
    backend.get_or_create_collection("papers")
    assert backend.list_documents("papers") == []


def test_unsupported_file_type_raises(backend, tmp_path):
    backend.get_or_create_collection("papers")
    bad_file = tmp_path / "test.xyz"
    bad_file.write_text("hello")
    with pytest.raises(FileTypeError):
        backend.add_document("papers", str(bad_file))


def test_register_custom_parser(backend):
    from pageindex.parser.protocol import ParsedDocument, ContentNode

    class TxtParser:
        def supported_extensions(self):
            return [".txt"]
        def parse(self, file_path, **kwargs):
            text = Path(file_path).read_text()
            return ParsedDocument(doc_name="test", nodes=[
                ContentNode(content=text, tokens=len(text.split()), title="Content", index=1, level=1)
            ])

    backend.register_parser(TxtParser())
    # Now .txt should be supported (won't raise FileTypeError)
    assert backend._resolve_parser("test.txt") is not None
