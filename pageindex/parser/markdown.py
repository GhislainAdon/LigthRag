import re
from pathlib import Path
from .protocol import ContentNode, ParsedDocument
from ..index.utils import count_tokens


class MarkdownParser:
    def supported_extensions(self) -> list[str]:
        return [".md", ".markdown"]

    def parse(self, file_path: str, **kwargs) -> ParsedDocument:
        path = Path(file_path)
        model = kwargs.get("model")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        headers = self._extract_headers(lines)
        nodes = self._build_nodes(headers, lines, model)

        return ParsedDocument(doc_name=path.stem, nodes=nodes)

    def _extract_headers(self, lines: list[str]) -> list[dict]:
        header_pattern = r"^(#{1,6})\s+(.+)$"
        code_block_pattern = r"^```"
        headers = []
        in_code_block = False

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if re.match(code_block_pattern, stripped):
                in_code_block = not in_code_block
                continue
            if not in_code_block and stripped:
                match = re.match(header_pattern, stripped)
                if match:
                    headers.append({
                        "title": match.group(2).strip(),
                        "level": len(match.group(1)),
                        "line_num": line_num,
                    })
        return headers

    def _build_nodes(self, headers: list[dict], lines: list[str], model: str | None) -> list[ContentNode]:
        nodes = []
        for i, header in enumerate(headers):
            start = header["line_num"] - 1
            end = headers[i + 1]["line_num"] - 1 if i + 1 < len(headers) else len(lines)
            text = "\n".join(lines[start:end]).strip()
            tokens = count_tokens(text, model=model)
            nodes.append(ContentNode(
                content=text,
                tokens=tokens,
                title=header["title"],
                index=header["line_num"],
                level=header["level"],
            ))
        return nodes
