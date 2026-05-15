import pytest

from pageindex.backend.cloud import CloudBackend, API_BASE


def test_cloud_backend_init():
    backend = CloudBackend(api_key="pi-test")
    assert backend._api_key == "pi-test"
    assert backend._headers["api_key"] == "pi-test"


def test_api_base_url():
    assert "pageindex.ai" in API_BASE


def test_query_rejects_empty_doc_ids():
    backend = CloudBackend(api_key="pi-test")
    with pytest.raises(ValueError, match="cannot be empty"):
        backend.query("col", "q", doc_ids=[])
