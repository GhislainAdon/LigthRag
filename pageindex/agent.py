# pageindex/agent.py
from __future__ import annotations
from typing import AsyncIterator
from .events import QueryEvent
from .backend.protocol import AgentTools


SYSTEM_PROMPT = """
You are PageIndex, a document QA assistant.
TOOL USE:
- Call list_documents() to see available documents.
- Call get_document(doc_id) to confirm status and page/line count.
- Call get_document_structure(doc_id) to identify relevant page ranges.
- Call get_page_content(doc_id, pages="5-7") with tight ranges; never fetch the whole document.
- Before each tool call, output one short sentence explaining the reason.
IMAGES:
- Page content may contain image references like ![image](path). Always preserve these in your answer so the downstream UI can render them.
- Place images near the relevant context in your answer.
Answer based only on tool output. Be concise.
"""


class QueryStream:
    """Streaming query result, similar to OpenAI's RunResultStreaming.

    Usage:
        stream = col.query("question", stream=True)
        async for event in stream:
            if event.type == "answer_delta":
                print(event.data, end="", flush=True)
    """

    def __init__(self, tools: AgentTools, question: str, model: str = None):
        from agents import Agent
        from agents.model_settings import ModelSettings
        self._agent = Agent(
            name="PageIndex",
            instructions=SYSTEM_PROMPT,
            tools=tools.function_tools,
            mcp_servers=tools.mcp_servers,
            model=model,
            model_settings=ModelSettings(parallel_tool_calls=False),
        )
        self._question = question

    async def stream_events(self) -> AsyncIterator[QueryEvent]:
        """Async generator yielding QueryEvent as they arrive."""
        from agents import Runner, ItemHelpers
        from agents.stream_events import RawResponsesStreamEvent, RunItemStreamEvent
        from openai.types.responses import ResponseTextDeltaEvent

        streamed_run = Runner.run_streamed(self._agent, self._question)
        async for event in streamed_run.stream_events():
            if isinstance(event, RawResponsesStreamEvent):
                if isinstance(event.data, ResponseTextDeltaEvent):
                    yield QueryEvent(type="answer_delta", data=event.data.delta)
            elif isinstance(event, RunItemStreamEvent):
                item = event.item
                if item.type == "tool_call_item":
                    raw = item.raw_item
                    yield QueryEvent(type="tool_call", data={
                        "name": raw.name, "args": getattr(raw, "arguments", "{}"),
                    })
                elif item.type == "tool_call_output_item":
                    yield QueryEvent(type="tool_result", data=str(item.output))
                elif item.type == "message_output_item":
                    text = ItemHelpers.text_message_output(item)
                    if text:
                        yield QueryEvent(type="answer_done", data=text)

    def __aiter__(self):
        return self.stream_events()


class AgentRunner:
    def __init__(self, tools: AgentTools, model: str = None):
        self._tools = tools
        self._model = model

    def run(self, question: str) -> str:
        """Sync non-streaming query. Returns answer string."""
        from agents import Agent, Runner
        from agents.model_settings import ModelSettings
        agent = Agent(
            name="PageIndex",
            instructions=SYSTEM_PROMPT,
            tools=self._tools.function_tools,
            mcp_servers=self._tools.mcp_servers,
            model=self._model,
            model_settings=ModelSettings(parallel_tool_calls=False),
        )
        result = Runner.run_sync(agent, question)
        return result.final_output
