import json

import pytest


def test_insert_files_does_not_disable_sqlite_synchronous(tmp_path):
    from pageindex.filesystem.store import SQLiteFileSystemStore

    statements = []

    class RecordingStore(SQLiteFileSystemStore):
        def connect(self):
            conn = super().connect()
            conn.set_trace_callback(statements.append)
            return conn

    store = RecordingStore(tmp_path / "workspace")
    statements.clear()

    store.insert_files(
        [
            {
                "file_ref": "ref_report",
                "external_id": "doc_report",
                "storage_uri": "file:///tmp/report.pdf",
                "folder_path": "/documents",
                "title": "Report",
                "descriptor": "documents/report.pdf",
                "content_type": "application/pdf",
                "source_type": "documents",
                "fingerprint": "fingerprint",
                "text_artifact_path": "artifacts/text/ref_report.txt",
                "raw_artifact_path": None,
                "metadata": {},
                "metadata_json": json.dumps({}),
                "metadata_text": "",
                "content": "",
                "skip_fts": True,
            }
        ]
    )

    assert not any(
        statement.upper().replace(" ", "") == "PRAGMASYNCHRONOUS=OFF"
        for statement in statements
    )


def test_metadata_numeric_filters_compare_numeric_encodings(tmp_path):
    from pageindex.filesystem import PageIndexFileSystem

    filesystem = PageIndexFileSystem(tmp_path / "workspace")
    filesystem.metadata.register_schema({"fields": {"score": "number"}})
    filesystem.register_file(
        storage_uri="file:///tmp/int.txt",
        folder_path="/documents",
        external_id="doc_int",
        title="Int",
        content="int body",
        metadata={"score": 3},
    )
    filesystem.register_file(
        storage_uri="file:///tmp/float.txt",
        folder_path="/documents",
        external_id="doc_float",
        title="Float",
        content="float body",
        metadata={"score": 3.0},
    )
    filesystem.register_file(
        storage_uri="file:///tmp/text.txt",
        folder_path="/documents",
        external_id="doc_text",
        title="Text",
        content="text body",
        metadata={"score": "3"},
    )

    eq_rows = filesystem.search(None, metadata_filter={"score": {"$eq": 3}})
    in_rows = filesystem.search(None, metadata_filter={"score": {"$in": [3.0]}})
    ne_rows = filesystem.search(None, metadata_filter={"score": {"$ne": 3}})

    assert {row.external_id for row in eq_rows} == {
        "doc_int",
        "doc_float",
        "doc_text",
    }
    assert {row.external_id for row in in_rows} == {
        "doc_int",
        "doc_float",
        "doc_text",
    }
    assert ne_rows == []


def test_metadata_range_filters_include_text_numbers_and_preserve_large_ints(tmp_path):
    from pageindex.filesystem import PageIndexFileSystem

    huge = 9007199254740993
    filesystem = PageIndexFileSystem(tmp_path / "workspace")
    filesystem.metadata.register_schema({"fields": {"score": "number"}})
    filesystem.register_file(
        storage_uri="file:///tmp/text-num.txt",
        folder_path="/documents",
        external_id="doc_text_num",
        title="Text numeric",
        content="text numeric body",
        metadata={"score": "3"},
    )
    filesystem.register_file(
        storage_uri="file:///tmp/huge-low.txt",
        folder_path="/documents",
        external_id="doc_huge_low",
        title="Huge low",
        content="huge low body",
        metadata={"score": huge},
    )
    filesystem.register_file(
        storage_uri="file:///tmp/huge-high.txt",
        folder_path="/documents",
        external_id="doc_huge_high",
        title="Huge high",
        content="huge high body",
        metadata={"score": huge + 2},
    )

    text_rows = filesystem.search(None, metadata_filter={"score": {"$gte": 2}})
    huge_rows = filesystem.search(None, metadata_filter={"score": {"$gt": huge + 1}})

    assert "doc_text_num" in {row.external_id for row in text_rows}
    assert {row.external_id for row in huge_rows} == {"doc_huge_high"}


def test_register_file_rejects_parent_directory_segments(tmp_path):
    from pageindex.filesystem import PageIndexFileSystem

    filesystem = PageIndexFileSystem(tmp_path / "workspace")

    with pytest.raises(ValueError, match="must not contain '\\.\\.'"):
        filesystem.register_file(
            storage_uri="file:///tmp/report.txt",
            folder_path="/a/../b",
            external_id="doc_bad",
            title="Bad",
            content="bad body",
        )


def test_file_upsert_preserves_created_at(tmp_path):
    from pageindex.filesystem import PageIndexFileSystem

    filesystem = PageIndexFileSystem(tmp_path / "workspace")
    file_ref = filesystem.register_file(
        storage_uri="file:///tmp/report-v1.txt",
        folder_path="/documents",
        external_id="doc_report",
        title="Report",
        content="version one",
    )
    with filesystem.store.connect() as conn:
        conn.execute(
            "UPDATE files SET created_at = '2001-02-03 04:05:06' WHERE file_ref = ?",
            (file_ref,),
        )
    filesystem.register_file(
        storage_uri="file:///tmp/report-v2.txt",
        folder_path="/documents",
        external_id="doc_report",
        title="Report",
        content="version two",
    )

    with filesystem.store.connect() as conn:
        row = conn.execute(
            "SELECT created_at, storage_uri, deleted_at FROM files WHERE file_ref = ?",
            (file_ref,),
        ).fetchone()

    assert row["created_at"] == "2001-02-03 04:05:06"
    assert row["storage_uri"] == "file:///tmp/report-v2.txt"
    assert row["deleted_at"] is None


def test_file_upsert_preserves_soft_delete_tombstone(tmp_path):
    from pageindex.filesystem import PageIndexFileSystem

    filesystem = PageIndexFileSystem(tmp_path / "workspace")
    file_ref = filesystem.register_file(
        storage_uri="file:///tmp/report-v1.txt",
        folder_path="/documents",
        external_id="doc_report",
        title="Report",
        content="version one",
    )
    with filesystem.store.connect() as conn:
        conn.execute(
            "UPDATE files SET deleted_at = '2001-02-03 04:05:06' WHERE file_ref = ?",
            (file_ref,),
        )
    filesystem.register_file(
        storage_uri="file:///tmp/report-v2.txt",
        folder_path="/documents",
        external_id="doc_report",
        title="Report",
        content="version two",
    )

    with filesystem.store.connect() as conn:
        row = conn.execute(
            "SELECT storage_uri, deleted_at FROM files WHERE file_ref = ?",
            (file_ref,),
        ).fetchone()

    assert row["storage_uri"] == "file:///tmp/report-v2.txt"
    assert row["deleted_at"] == "2001-02-03 04:05:06"
    assert filesystem.search(None) == []


def test_listing_uses_one_consistent_folder_membership_row(tmp_path):
    from pageindex.filesystem import PageIndexFileSystem

    filesystem = PageIndexFileSystem(tmp_path / "workspace")
    file_ref = filesystem.register_file(
        storage_uri="file:///tmp/shared.txt",
        folder_path="/a",
        external_id="doc_shared",
        title="Original",
        content="shared body",
    )
    filesystem.store.attach_file_to_folder(
        file_ref,
        "/b",
        metadata={"display_name": "Alpha"},
    )

    listing = filesystem.browse("/", recursive=True, limit=10)
    row = next(item for item in listing["files"] if item["external_id"] == "doc_shared")

    assert row["folder_path"] == "/a"
    assert row["title"] == "Original"
