"""表达式求值。"""

from __future__ import annotations

from obox.ui.expr import evaluate, format_value, is_truthy


def test_paths_and_length() -> None:
    scope = {"apps": [1, 2], "app": {"title": "A"}}
    assert evaluate("apps.length", scope) == 2
    assert evaluate("app.title", scope) == "A"
    assert evaluate("missing.deep", scope) is None


def test_literals_and_comparisons() -> None:
    scope = {"n": 2, "empty": [], "flag": False}
    assert evaluate("n > 1", scope) is True
    assert evaluate("n == 2 && n != 3", scope) is True
    assert evaluate("!empty.length", scope) is True
    assert evaluate("flag || n == 2", scope) is True
    assert evaluate("'x' == 'x'", scope) is True


def test_truthy_and_format() -> None:
    assert is_truthy([1]) and not is_truthy([])
    assert is_truthy("a") and not is_truthy("")
    assert format_value(None) == ""
    assert format_value(True) == "true"
    assert format_value(2.0) == "2"
