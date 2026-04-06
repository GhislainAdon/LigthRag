from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class ContentNode:
    """Universal content unit produced by parsers."""
    content: str
    tokens: int
    title: str | None = None
    index: int | None = None
    level: int | None = None
    images: list[dict] | None = None  # [{"path": str, "width": int, "height": int}, ...]


@dataclass
class ParsedDocument:
    """Unified parser output. Always a flat list of ContentNode."""
    doc_name: str
    nodes: list[ContentNode]
    metadata: dict | None = None


@runtime_checkable
class DocumentParser(Protocol):
    def supported_extensions(self) -> list[str]: ...
    def parse(self, file_path: str, **kwargs) -> ParsedDocument: ...
