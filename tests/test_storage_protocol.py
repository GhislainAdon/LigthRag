from pageindex.storage.protocol import StorageEngine

def test_storage_engine_is_protocol():
    class FakeStorage:
        def create_collection(self, name: str) -> None: pass
        def get_or_create_collection(self, name: str) -> None: pass
        def list_collections(self) -> list[str]: return []
        def delete_collection(self, name: str) -> None: pass
        def save_document(self, collection: str, doc_id: str, doc: dict) -> None: pass
        def find_document_by_hash(self, collection: str, file_hash: str) -> str | None: return None
        def get_document(self, collection: str, doc_id: str) -> dict: return {}
        def get_document_structure(self, collection: str, doc_id: str) -> dict: return {}
        def get_pages(self, collection: str, doc_id: str) -> list | None: return None
        def list_documents(self, collection: str) -> list[dict]: return []
        def delete_document(self, collection: str, doc_id: str) -> None: pass
        def close(self) -> None: pass

    storage = FakeStorage()
    assert isinstance(storage, StorageEngine)
