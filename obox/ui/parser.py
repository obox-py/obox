"""把 HTML 组件片段解析成节点树。"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser

from ..api.errors import OboxError


class ParseError(OboxError):
    code = "E_PARSE"


@dataclass
class Node:
    """一个组件标签或一段文本。"""

    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list["Node | str"] = field(default_factory=list)
    line: int = 0
    col: int = 0

    @property
    def component_id(self) -> str:
        return self.attrs.get("id", "")

    def text(self) -> str:
        parts = [child for child in self.children if isinstance(child, str)]
        return "".join(parts).strip()


class _Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.roots: list[Node] = []
        self._stack: list[Node] = []
        self.errors: list[ParseError] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line, col = self.getpos()
        node = Node(tag=tag, attrs={key: value or "" for key, value in attrs}, line=line, col=col)
        self._append(node)
        self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line, col = self.getpos()
        self._append(Node(tag=tag, attrs={key: value or "" for key, value in attrs}, line=line, col=col))

    def handle_endtag(self, tag: str) -> None:
        if not self._stack:
            line, col = self.getpos()
            self.errors.append(ParseError(f"第 {line} 行第 {col} 列：多余的结束标签 {tag}"))
            return
        current = self._stack[-1]
        if current.tag != tag:
            line, col = self.getpos()
            self.errors.append(
                ParseError(f"第 {line} 行第 {col} 列：结束标签 {tag} 与开始标签 {current.tag} 不匹配")
            )
            return
        self._stack.pop()

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        if not self._stack:
            self.errors.append(ParseError(f"文本出现在组件之外：{data.strip()[:20]!r}"))
            return
        self._stack[-1].children.append(data)

    def _append(self, node: Node) -> None:
        if self._stack:
            self._stack[-1].children.append(node)
        else:
            self.roots.append(node)


def parse_fragment(source: str) -> list[Node]:
    """解析一段片段；出现结构性错误时抛 ParseError。"""
    parser = _Parser()
    parser.feed(source)
    parser.close()
    if parser.errors:
        raise parser.errors[0]
    if parser._stack:
        unclosed = parser._stack[-1]
        raise ParseError(f"第 {unclosed.line} 行：标签 {unclosed.tag} 没有闭合")
    return parser.roots
