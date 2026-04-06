from pageindex.backend.cloud import CloudBackend, API_BASE


def test_cloud_backend_init():
    backend = CloudBackend(api_key="pi-test")
    assert backend._api_key == "pi-test"
    assert backend._headers["api_key"] == "pi-test"


def test_api_base_url():
    assert "pageindex.ai" in API_BASE


def test_get_retrieve_model_is_none():
    backend = CloudBackend(api_key="pi-test")
    assert backend.get_agent_tools("col").function_tools == []
