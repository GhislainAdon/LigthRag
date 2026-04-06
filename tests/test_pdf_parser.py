import pytest
from pathlib import Path
from pageindex.parser.pdf import PdfParser
from pageindex.parser.protocol import ContentNode, ParsedDocument

TEST_PDF = Path("tests/pdfs/deepseek-r1.pdf")

def test_supported_extensions():
    parser = PdfParser()
    assert ".pdf" in parser.supported_extensions()

@pytest.mark.skipif(not TEST_PDF.exists(), reason="Test PDF not available")
def test_parse_returns_parsed_document():
    parser = PdfParser()
    result = parser.parse(str(TEST_PDF))
    assert isinstance(result, ParsedDocument)
    assert len(result.nodes) > 0
    assert result.doc_name != ""

@pytest.mark.skipif(not TEST_PDF.exists(), reason="Test PDF not available")
def test_parse_nodes_are_flat_without_level():
    parser = PdfParser()
    result = parser.parse(str(TEST_PDF))
    for node in result.nodes:
        assert isinstance(node, ContentNode)
        assert node.content is not None
        assert node.tokens >= 0
        assert node.index is not None
        assert node.level is None
