from dataclasses import dataclass
from typing import Literal, Any


@dataclass
class QueryEvent:
    """Event emitted during streaming query."""
    type: Literal["reasoning", "tool_call", "tool_result", "answer_delta", "answer_done"]
    data: Any
