from pageindex.agent import AgentRunner, SYSTEM_PROMPT
from pageindex.backend.protocol import AgentTools


def test_agent_runner_init():
    tools = AgentTools(function_tools=["mock_tool"])
    runner = AgentRunner(tools=tools, model="gpt-4o")
    assert runner._model == "gpt-4o"


def test_system_prompt_has_tool_instructions():
    assert "list_documents" in SYSTEM_PROMPT
    assert "get_document_structure" in SYSTEM_PROMPT
    assert "get_page_content" in SYSTEM_PROMPT
