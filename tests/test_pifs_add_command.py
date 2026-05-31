import json
from pathlib import Path

import pytest


class GeneratedMetadata:
    def __init__(self):
        self.calls = []

    def generate(self, request, *, fields):
        self.calls.append((request, list(fields)))
        values = {
            "summary": f"Summary for {request.title}: {request.text[:60]}",
            "doc_type": "uploaded_file",
            "domain": "workspace",
            "topic": "pifs add",
        }
        return {field: values[field] for field in fields if field in values}


class RecordingSummaryIndexer:
    def __init__(self):
        self.upserted = []

    def upsert_summary(self, record):
        self.upserted.append(dict(record))
        return {"status": "ready", "indexed_rows": 1}


def write_pageindex_client_doc(workspace: Path, doc_id: str, doc: dict) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / f"{doc_id}.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    meta = {
        doc_id: {
            "type": doc.get("type", ""),
            "doc_name": doc.get("doc_name", ""),
            "doc_description": doc.get("doc_description", ""),
            "path": doc.get("path", ""),
            "line_count": doc.get("line_count"),
        }
    }
    (workspace / "_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_add_text_folder_target_copies_artifact_indexes_summary_and_is_readable(tmp_path):
    from pageindex.filesystem import PIFSCommandExecutor, PageIndexFileSystem

    source = tmp_path / "filing.txt"
    source.write_text("alpha filing text for pifs add", encoding="utf-8")
    indexer = RecordingSummaryIndexer()
    filesystem = PageIndexFileSystem(
        workspace=tmp_path / "workspace",
        metadata_generator=GeneratedMetadata(),
        summary_projection_indexer=indexer,
    )

    info = filesystem.add_file(str(source), "/documents/reports")

    assert info["source_path"] == "documents/reports/filing.txt"
    assert info["folder_path"] == "/documents/reports"
    assert filesystem.folder_info("/documents/reports")["path"] == "/documents/reports"
    assert info["storage_uri"] != source.as_uri()
    assert "/artifacts/uploads/" in info["storage_uri"]
    copied_path = Path(info["storage_uri"].removeprefix("file://"))
    assert copied_path.read_text(encoding="utf-8") == "alpha filing text for pifs add"
    assert copied_path.resolve() != source.resolve()

    executor = PIFSCommandExecutor(filesystem, json_output=True)
    rendered = json.loads(executor.execute("cat /documents/reports/filing.txt --all"))

    assert rendered["data"]["text"] == "alpha filing text for pifs add"
    assert info["metadata"]["summary"].startswith("Summary for filing.txt")
    assert indexer.upserted[0]["file_ref"] == info["file_ref"]
    assert indexer.upserted[0]["metadata"]["summary"] == info["metadata"]["summary"]


def test_add_rejects_same_folder_same_basename_without_overwrite(tmp_path):
    from pageindex.filesystem import PIFSCommandExecutor, PageIndexFileSystem

    source = tmp_path / "conflict.txt"
    source.write_text("first body", encoding="utf-8")
    filesystem = PageIndexFileSystem(
        workspace=tmp_path / "workspace",
        metadata_generator=GeneratedMetadata(),
        summary_projection_indexer=RecordingSummaryIndexer(),
    )

    filesystem.add_file(source, "/documents")
    source.write_text("second body must not overwrite", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        filesystem.add_file(source, "/documents")

    executor = PIFSCommandExecutor(filesystem, json_output=True)
    rendered = json.loads(executor.execute("cat /documents/conflict.txt --all"))
    assert rendered["data"]["text"] == "first body"


def test_add_rejects_unsupported_type_before_registration(tmp_path):
    from pageindex.filesystem import PageIndexFileSystem

    source = tmp_path / "payload.json"
    source.write_text('{"unsupported": true}', encoding="utf-8")
    filesystem = PageIndexFileSystem(
        workspace=tmp_path / "workspace",
        metadata_generator=GeneratedMetadata(),
        summary_projection_indexer=RecordingSummaryIndexer(),
    )

    with pytest.raises(ValueError, match="Unsupported file type"):
        filesystem.add_file(source, "/documents")

    assert filesystem.browse("/", recursive=True)["files"] == []
    assert not list((tmp_path / "workspace" / "artifacts" / "uploads").glob("**/*"))


def test_add_markdown_builds_pageindex_tree_from_copied_artifact(tmp_path, monkeypatch):
    from pageindex import PageIndexClient
    from pageindex.filesystem import PIFSCommandExecutor, PageIndexFileSystem

    indexed_paths = []

    def fake_index(self, file_path, mode="auto"):
        indexed_paths.append(Path(file_path))
        doc_id = "doc_added_md"
        doc = {
            "id": doc_id,
            "type": "md",
            "path": str(Path(file_path).resolve()),
            "doc_name": "notes.md",
            "doc_description": "",
            "line_count": 3,
            "structure": [
                {
                    "title": "Notes",
                    "node_id": "0001",
                    "line_num": 1,
                    "text": "# Notes\n\ncopied markdown body",
                    "nodes": [],
                }
            ],
        }
        write_pageindex_client_doc(self.workspace, doc_id, doc)
        self.documents[doc_id] = doc
        return doc_id

    monkeypatch.setattr(PageIndexClient, "index", fake_index)
    source = tmp_path / "notes.md"
    source.write_text("# Notes\n\ncopied markdown body", encoding="utf-8")
    filesystem = PageIndexFileSystem(
        workspace=tmp_path / "workspace",
        metadata_generator=GeneratedMetadata(),
        summary_projection_indexer=RecordingSummaryIndexer(),
    )

    info = filesystem.add_file(source, "/documents")
    executor = PIFSCommandExecutor(filesystem, json_output=True)
    structure = json.loads(executor.execute("cat /documents/notes.md --structure"))

    assert structure["data"]["available"] is True
    assert structure["data"]["structure"][0]["title"] == "Notes"
    assert indexed_paths == [Path(info["storage_uri"].removeprefix("file://"))]
    assert indexed_paths[0].resolve() != source.resolve()


def test_add_failure_does_not_leave_visible_catalog_or_artifacts(tmp_path, monkeypatch):
    from pageindex.filesystem import PageIndexFileSystem

    source = tmp_path / "atomic.txt"
    source.write_text("atomic body", encoding="utf-8")
    filesystem = PageIndexFileSystem(
        workspace=tmp_path / "workspace",
        metadata_generator=GeneratedMetadata(),
        summary_projection_indexer=RecordingSummaryIndexer(),
    )

    def fail_insert(records):
        raise RuntimeError("catalog insert failed")

    monkeypatch.setattr(filesystem.store, "insert_files", fail_insert)

    with pytest.raises(RuntimeError, match="catalog insert failed"):
        filesystem.add_file(source, "/documents")

    assert filesystem.browse("/", recursive=True)["files"] == []
    assert not list((tmp_path / "workspace" / "artifacts" / "uploads").glob("**/*"))
    assert not list((tmp_path / "workspace" / "artifacts" / "text").glob("*.txt"))
    assert not list((tmp_path / "workspace" / "artifacts" / "raw").glob("*.json"))


def test_cli_add_uses_workspace_and_prints_added_file(monkeypatch, capsys, tmp_path):
    from pageindex.filesystem import cli

    source = tmp_path / "cli.txt"
    source.write_text("cli body", encoding="utf-8")
    calls = []

    class FakeAddFileSystem:
        def __init__(self, workspace):
            self.workspace = Path(workspace)

        def configure_existing_projection_retrieval(self):
            return False

        def add_file(self, physical_path, virtual_target):
            calls.append((self.workspace, physical_path, virtual_target))
            return {
                "file_ref": "file_cli",
                "path": "/documents/cli.txt",
                "source_path": "documents/cli.txt",
                "storage_uri": "file:///workspace/artifacts/uploads/file_cli/cli.txt",
            }

    monkeypatch.setattr(cli, "PageIndexFileSystem", FakeAddFileSystem)

    status = cli.main(["--workspace", str(tmp_path / "workspace"), "add", str(source), "/documents"])

    assert status == 0
    assert calls == [(tmp_path / "workspace", str(source), "/documents")]
    assert capsys.readouterr().out == (
        "added: /documents/cli.txt\n"
        "file_ref: file_cli\n"
        "storage_uri: file:///workspace/artifacts/uploads/file_cli/cli.txt\n"
    )
