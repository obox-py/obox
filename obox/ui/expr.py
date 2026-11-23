"""极简表达式：路径、length、字面量、比较与 !。

模板里只允许这一层：不支持函数调用、算术与下标，够 o-for/o-if/绑定使用。
"""

from __future__ import annotations

import re
from typing import Any

_TOKEN = re.compile(
    r"""\s*(?:
        (?P<number>\d+(?:\.\d+)?)
      | (?P<string>'[^']*'|"[^"]*")
      | (?P<op>==|!=|>=|<=|&&|\|\||>|<|!)
      | (?P<path>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)
      | (?P<word>true|false|null)
    )""",
    re.VERBOSE,
)


class ExprError(Exception):
    """表达式非法。"""


def _tokenize(source: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    position = 0
    while position < len(source):
        if source[position].isspace():
            position += 1
            continue
        match = _TOKEN.match(source, position)
        if match is None:
            raise ExprError(f"无法解析的表达式：{source[position:]}")
        kind = match.lastgroup or ""
        tokens.append((kind, match.group(kind)))
        position = match.end()
    return tokens


def _lookup(path: str, scope: dict[str, Any]) -> Any:
    parts = path.split(".")
    value: Any = scope.get(parts[0])
    for part in parts[1:]:
        if value is None:
            return None
        if part == "length":
            try:
                return len(value)
            except TypeError:
                return None
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = getattr(value, part, None)
    return value


def evaluate(source: str, scope: dict[str, Any] | None = None) -> Any:
    scope = scope or {}
    tokens = _tokenize(source)
    if not tokens:
        return None
    position = 0

    def peek() -> tuple[str, str] | None:
        return tokens[position] if position < len(tokens) else None

    def take() -> tuple[str, str]:
        nonlocal position
        token = tokens[position]
        position += 1
        return token

    def parse_primary() -> Any:
        token = peek()
        if token is None:
            raise ExprError("表达式不完整")
        kind, text = take()
        if kind == "number":
            return float(text) if "." in text else int(text)
        if kind == "string":
            return text[1:-1]
        if kind == "word":
            return {"true": True, "false": False, "null": None}[text]
        if kind == "path":
            return _lookup(text, scope)
        raise ExprError(f"意外的记号：{text}")

    def parse_unary() -> Any:
        token = peek()
        if token == ("op", "!"):
            take()
            return not parse_unary()
        return parse_primary()

    def parse_compare() -> Any:
        left = parse_unary()
        token = peek()
        if token and token[0] == "op" and token[1] in {"==", "!=", ">", "<", ">=", "<="}:
            _, operator = take()
            right = parse_unary()
            if operator == "==":
                return left == right
            if operator == "!=":
                return left != right
            if operator == ">":
                return _as_number(left) > _as_number(right)
            if operator == "<":
                return _as_number(left) < _as_number(right)
            if operator == ">=":
                return _as_number(left) >= _as_number(right)
            return _as_number(left) <= _as_number(right)
        return left

    def parse_and() -> Any:
        value = parse_compare()
        while peek() == ("op", "&&"):
            take()
            right = parse_compare()
            value = bool(value) and bool(right)
        return value

    def parse_or() -> Any:
        value = parse_and()
        while peek() == ("op", "||"):
            take()
            right = parse_and()
            value = bool(value) or bool(right)
        return value

    result = parse_or()
    if position != len(tokens):
        raise ExprError(f"多余的记号：{tokens[position][1]}")
    return result


def _as_number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def is_truthy(value: Any) -> bool:
    if isinstance(value, (list, tuple, dict, str)):
        return len(value) > 0
    return bool(value)


def format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
