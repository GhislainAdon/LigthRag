# pageindex/config.py
from __future__ import annotations

import os

from pydantic import BaseModel


class IndexConfig(BaseModel):
    """Configuration for the PageIndex indexing pipeline.

    All fields have sensible defaults. Advanced users can override
    via LocalClient(index_config=IndexConfig(...)) or a dict.
    """
    model_config = {"extra": "forbid"}

    model: str = "gpt-4o-2024-11-20"
    retrieve_model: str | None = None
    toc_check_page_num: int = 20
    max_page_num_each_node: int = 10
    max_token_num_each_node: int = 20000
    if_add_node_id: bool = True
    if_add_node_summary: bool = True
    if_add_doc_description: bool = True
    if_add_node_text: bool = False


def _env_drop_params_default() -> bool:
    return os.getenv("PAGEINDEX_DROP_PARAMS", "true").strip().lower() not in (
        "0", "false", "no", "off",
    )


# Per-call kwargs PageIndex passes to every litellm completion. These are
# PageIndex-OWNED and applied PER CALL — never written to litellm's shared module
# globals, so they don't leak into other libraries sharing the litellm module.
# Defaults preserve historical behavior: temperature=0 keeps structure
# extraction deterministic; drop_params=True lets a provider that rejects a param
# (e.g. temperature on some local / reasoning models) succeed by dropping it.
# Override/extend via set_llm_params(); the common drop_params case also has the
# PAGEINDEX_DROP_PARAMS env shortcut.
_LLM_PARAMS: dict = {"temperature": 0, "drop_params": _env_drop_params_default()}

# Structural kwargs PageIndex always supplies itself — not overridable here.
_RESERVED_LLM_PARAMS = ("model", "messages")


def get_llm_params() -> dict:
    """Return a copy of the per-call kwargs PageIndex passes to litellm."""
    return dict(_LLM_PARAMS)


def set_llm_params(**kwargs) -> None:
    """Override or extend the litellm completion kwargs PageIndex sends per call.

    e.g. ``set_llm_params(drop_params=False, temperature=1, num_retries=5)``.
    Applied per call; never writes litellm's global state, so it can't leak into
    other litellm users in the same process. ``model`` / ``messages`` are
    reserved (PageIndex supplies them) and rejected.
    """
    reserved = [k for k in kwargs if k in _RESERVED_LLM_PARAMS]
    if reserved:
        raise ValueError(f"cannot override reserved litellm kwargs: {reserved}")
    _LLM_PARAMS.update(kwargs)
