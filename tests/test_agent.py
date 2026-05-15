from pageindex.agent import AgentRunner, OPEN_SYSTEM_PROMPT, SCOPED_SYSTEM_PROMPT
from pageindex.backend.protocol import AgentTools


def test_agent_runner_init():
    tools = AgentTools(function_tools=["mock_tool"])
    runner = AgentRunner(tools=tools, model="gpt-4o")
    assert runner._model == "gpt-4o"


def test_open_prompt_has_tool_instructions():
    assert "list_documents" in OPEN_SYSTEM_PROMPT
    assert "get_document_structure" in OPEN_SYSTEM_PROMPT
    assert "get_page_content" in OPEN_SYSTEM_PROMPT


def test_scoped_prompt_omits_list_documents():
    assert "list_documents" not in SCOPED_SYSTEM_PROMPT
    assert "get_document_structure" in SCOPED_SYSTEM_PROMPT
    assert "get_page_content" in SCOPED_SYSTEM_PROMPT
