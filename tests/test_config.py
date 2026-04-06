# tests/test_config.py
import pytest
from pageindex.config import IndexConfig


def test_defaults():
    config = IndexConfig()
    assert config.model == "gpt-4o-2024-11-20"
    assert config.retrieve_model is None
    assert config.toc_check_page_num == 20


def test_overrides():
    config = IndexConfig(model="gpt-5.4", retrieve_model="claude-sonnet")
    assert config.model == "gpt-5.4"
    assert config.retrieve_model == "claude-sonnet"


def test_unknown_key_raises():
    with pytest.raises(Exception):
        IndexConfig(nonexistent_key="value")


def test_model_copy_with_update():
    config = IndexConfig(toc_check_page_num=30)
    updated = config.model_copy(update={"model": "gpt-5.4"})
    assert updated.model == "gpt-5.4"
    assert updated.toc_check_page_num == 30
