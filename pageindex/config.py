# pageindex/config.py
from __future__ import annotations
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
