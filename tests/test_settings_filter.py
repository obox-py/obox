"""设置页过滤函数。"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location("settings_ext", Path("extensions/settings/extension.py"))
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
filter_groups = _MODULE.filter_groups

GROUPS = [
    {"id": "appearance", "title": "外观", "items": [{"key": "obox.theme", "title": "主题"}]},
    {"id": "language", "title": "语言", "items": [{"key": "obox.language", "title": "界面语言"}]},
    {"id": "about", "title": "关于", "items": [{"key": "obox.version", "title": "版本"}]},
]


def test_empty_returns_all() -> None:
    assert filter_groups(GROUPS, "") == GROUPS
    assert filter_groups(GROUPS, "  ") == GROUPS


def test_group_title_match_keeps_items() -> None:
    result = filter_groups(GROUPS, "外观")
    assert [group["id"] for group in result] == ["appearance"]
    assert result[0]["items"]


def test_item_title_match() -> None:
    result = filter_groups(GROUPS, "语言")
    assert [group["id"] for group in result] == ["language"]


def test_case_insensitive_and_no_match() -> None:
    assert filter_groups(GROUPS, "版本")
    assert filter_groups(GROUPS, "zzz") == []
