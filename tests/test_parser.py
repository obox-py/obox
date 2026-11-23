from __future__ import annotations

import pytest

from obox.ui.parser import ParseError, parse_fragment


def test_nested_nodes() -> None:
    nodes = parse_fragment('<Div id="a"><Text id="b" text="hi" /></Div>')
    assert nodes[0].tag == "div"
    assert nodes[0].children[0].component_id == "b"


def test_text_content_collected() -> None:
    nodes = parse_fragment('<Text id="a">你好</Text>')
    assert nodes[0].text() == "你好"


def test_unclosed_tag_rejected() -> None:
    with pytest.raises(ParseError):
        parse_fragment('<Div id="a">')


def test_mismatched_tag_rejected() -> None:
    with pytest.raises(ParseError):
        parse_fragment('<Div id="a"></Text>')


def test_text_outside_component_rejected() -> None:
    with pytest.raises(ParseError):
        parse_fragment("裸文本")
