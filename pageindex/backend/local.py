# pageindex/backend/local.py
import hashlib
import os
import re
import uuid
import shutil
from pathlib import Path

from ..parser.protocol import DocumentParser, ParsedDocument
from ..parser.pdf import PdfParser
from ..parser.markdown import MarkdownParser
from ..storage.protocol import StorageEngine
from ..index.pipeline import build_index
from ..index.utils import parse_pages, get_pdf_page_content, get_md_page_content, remove_fields
from ..backend.protocol import AgentTools
from ..errors import FileTypeError, DocumentNotFoundError, IndexingError, PageIndexError

_COLLECTION_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')


class LocalBackend:
    def __init__(self, storage: StorageEngine, files_dir: str, model: str = None,
                 retrieve_model: str = None, index_config=None):
        self._storage = storage
        self._files_dir = Path(files_dir)
        self._model = model
        self._retrieve_model = retrieve_model or model
        self._index_config = index_config
        self._parsers: list[DocumentParser] = [PdfParser(), MarkdownParser()]

    def register_parser(self, parser: DocumentParser) -> None:
        self._parsers.insert(0, parser)  # user parsers checked first

    def get_retrieve_model(self) -> str | None:
        return self._retrieve_model

    def _resolve_parser(self, file_path: str) -> DocumentParser:
        ext = os.path.splitext(file_path)[1].lower()
        for parser in self._parsers:
            if ext in parser.supported_extensions():
                return parser
        raise FileTypeError(f"No parser for extension: {ext}")

    # Collection management
    def _validate_collection_name(self, name: str) -> None:
        if not _COLLECTION_NAME_RE.match(name):
            raise PageIndexError(f"Invalid collection name: {name!r}. Must be 1-128 chars of [a-zA-Z0-9_-].")

    def create_collection(self, name: str) -> None:
        self._validate_collection_name(name)
        self._storage.create_collection(name)

    def get_or_create_collection(self, name: str) -> None:
        self._validate_collection_name(name)
        self._storage.get_or_create_collection(name)

    def list_collections(self) -> list[str]:
        return self._storage.list_collections()

    def delete_collection(self, name: str) -> None:
        self._storage.delete_collection(name)
        col_dir = self._files_dir / name
        if col_dir.exists():
            shutil.rmtree(col_dir)

    @staticmethod
    def _file_hash(file_path: str) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    # Document management
    def add_document(self, collection: str, file_path: str) -> str:
        file_path = os.path.realpath(file_path)
        if not os.path.isfile(file_path):
            raise FileTypeError(f"Not a regular file: {file_path}")
        parser = self._resolve_parser(file_path)

        # Dedup: skip if same file already indexed in this collection
        file_hash = self._file_hash(file_path)
        existing_id = self._storage.find_document_by_hash(collection, file_hash)
        if existing_id:
            return existing_id

        doc_id = str(uuid.uuid4())

        # Copy file to managed directory
        ext = os.path.splitext(file_path)[1]
        col_dir = self._files_dir / collection
        col_dir.mkdir(parents=True, exist_ok=True)
        managed_path = col_dir / f"{doc_id}{ext}"
        shutil.copy2(file_path, managed_path)

        try:
            # Store images alongside the document: files/{collection}/{doc_id}/images/
            images_dir = str(col_dir / doc_id / "images")
            parsed = parser.parse(file_path, model=self._model, images_dir=images_dir)
            result = build_index(parsed, model=self._model, opt=self._index_config)

            # Cache page text for fast retrieval (avoids re-reading files)
            pages = [{"page": n.index, "content": n.content,
                      **({"images": n.images} if n.images else {})}
                     for n in parsed.nodes if n.content]

            # Strip text from structure to save storage space (PDF only;
            # markdown needs text in structure for fallback retrieval)
            doc_type = ext.lstrip(".")
            if doc_type == "pdf":
                clean_structure = remove_fields(result["structure"], fields=["text"])
            else:
                clean_structure = result["structure"]

            self._storage.save_document(collection, doc_id, {
                "doc_name": parsed.doc_name,
                "doc_description": result.get("doc_description", ""),
                "file_path": str(managed_path),
                "file_hash": file_hash,
                "doc_type": doc_type,
                "structure": clean_structure,
                "pages": pages,
            })
        except Exception as e:
            managed_path.unlink(missing_ok=True)
            doc_dir = col_dir / doc_id
            if doc_dir.exists():
                shutil.rmtree(doc_dir)
            raise IndexingError(f"Failed to index {file_path}: {e}") from e

        return doc_id

    def get_document(self, collection: str, doc_id: str, include_text: bool = False) -> dict:
        """Get document metadata with structure.

        Args:
            include_text: If True, populate each structure node's 'text' field
                from cached page content. WARNING: may be very large — do NOT
                use in agent/LLM contexts as it can exhaust the context window.
        """
        doc = self._storage.get_document(collection, doc_id)
        if not doc:
            return {}
        doc["structure"] = self._storage.get_document_structure(collection, doc_id)
        if include_text:
            pages = self._storage.get_pages(collection, doc_id) or []
            page_map = {p["page"]: p["content"] for p in pages}
            self._fill_node_text(doc["structure"], page_map)
        return doc

    @staticmethod
    def _fill_node_text(nodes: list, page_map: dict) -> None:
        """Recursively fill 'text' on structure nodes from cached page content."""
        for node in nodes:
            start = node.get("start_index")
            end = node.get("end_index")
            if start is not None and end is not None:
                node["text"] = "\n".join(
                    page_map.get(p, "") for p in range(start, end + 1)
                )
            if "nodes" in node:
                LocalBackend._fill_node_text(node["nodes"], page_map)

    def get_document_structure(self, collection: str, doc_id: str) -> list:
        return self._storage.get_document_structure(collection, doc_id)

    def get_page_content(self, collection: str, doc_id: str, pages: str) -> list:
        doc = self._storage.get_document(collection, doc_id)
        if not doc:
            raise DocumentNotFoundError(f"Document {doc_id} not found")
        page_nums = parse_pages(pages)

        # Try cached pages first (fast, no file I/O)
        cached_pages = self._storage.get_pages(collection, doc_id)
        if cached_pages:
            return [p for p in cached_pages if p["page"] in page_nums]

        # Fallback to reading from file
        if doc["doc_type"] == "pdf":
            return get_pdf_page_content(doc["file_path"], page_nums)
        else:
            structure = self._storage.get_document_structure(collection, doc_id)
            return get_md_page_content(structure, page_nums)

    def list_documents(self, collection: str) -> list[dict]:
        return self._storage.list_documents(collection)

    def delete_document(self, collection: str, doc_id: str) -> None:
        doc = self._storage.get_document(collection, doc_id)
        if doc and doc.get("file_path"):
            Path(doc["file_path"]).unlink(missing_ok=True)
        # Clean up images directory: files/{collection}/{doc_id}/
        doc_dir = self._files_dir / collection / doc_id
        if doc_dir.exists():
            shutil.rmtree(doc_dir)
        self._storage.delete_document(collection, doc_id)

    def get_agent_tools(self, collection: str, doc_ids: list[str] | None = None) -> AgentTools:
        from agents import function_tool
        import json
        storage = self._storage
        col_name = collection
        backend = self
        filter_ids = doc_ids

        @function_tool
        def list_documents() -> str:
            """List all documents in the collection."""
            docs = storage.list_documents(col_name)
            if filter_ids:
                docs = [d for d in docs if d["doc_id"] in filter_ids]
            return json.dumps(docs)

        @function_tool
        def get_document(doc_id: str) -> str:
            """Get document metadata."""
            return json.dumps(storage.get_document(col_name, doc_id))

        @function_tool
        def get_document_structure(doc_id: str) -> str:
            """Get document tree structure (without text)."""
            structure = storage.get_document_structure(col_name, doc_id)
            return json.dumps(remove_fields(structure, fields=["text"]), ensure_ascii=False)

        @function_tool
        def get_page_content(doc_id: str, pages: str) -> str:
            """Get page content. Use tight ranges: '5-7', '3,8', '12'."""
            result = backend.get_page_content(col_name, doc_id, pages)
            return json.dumps(result, ensure_ascii=False)

        return AgentTools(function_tools=[list_documents, get_document, get_document_structure, get_page_content])

    def query(self, collection: str, question: str, doc_ids: list[str] | None = None) -> str:
        from ..agent import AgentRunner
        tools = self.get_agent_tools(collection, doc_ids)
        return AgentRunner(tools=tools, model=self._retrieve_model).run(question)

    async def query_stream(self, collection: str, question: str,
                           doc_ids: list[str] | None = None):
        from ..agent import QueryStream
        tools = self.get_agent_tools(collection, doc_ids)
        stream = QueryStream(tools=tools, question=question, model=self._retrieve_model)
        async for event in stream:
            yield event
