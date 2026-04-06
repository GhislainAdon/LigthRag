from pageindex.parser.protocol import ContentNode, ParsedDocument, DocumentParser


def test_content_node_required_fields():
    node = ContentNode(content="hello", tokens=5)
    assert node.content == "hello"
    assert node.tokens == 5
    assert node.title is None
    assert node.index is None
    assert node.level is None


def test_content_node_all_fields():
    node = ContentNode(content="# Intro", tokens=10, title="Intro", index=1, level=1)
    assert node.title == "Intro"
    assert node.index == 1
    assert node.level == 1


def test_parsed_document():
    nodes = [ContentNode(content="page1", tokens=100, index=1)]
    doc = ParsedDocument(doc_name="test.pdf", nodes=nodes)
    assert doc.doc_name == "test.pdf"
    assert len(doc.nodes) == 1
    assert doc.metadata is None


def test_parsed_document_with_metadata():
    nodes = [ContentNode(content="page1", tokens=100)]
    doc = ParsedDocument(doc_name="test.pdf", nodes=nodes, metadata={"author": "John"})
    assert doc.metadata["author"] == "John"


def test_document_parser_protocol():
    """Verify a class implementing DocumentParser is structurally compatible."""
    class MyParser:
        def supported_extensions(self) -> list[str]:
            return [".txt"]
        def parse(self, file_path: str, **kwargs) -> ParsedDocument:
            return ParsedDocument(doc_name="test", nodes=[])

    parser = MyParser()
    assert parser.supported_extensions() == [".txt"]
    result = parser.parse("test.txt")
    assert isinstance(result, ParsedDocument)
