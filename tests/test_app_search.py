"""App 扩展的过滤函数。"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location("app_ext", Path("extensions/app/extension.py"))
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
filter_apps = _MODULE.filter_apps

APPS = [
    {"id": "a", "title": "示范笔记", "description": "写东西", "author": "obox"},
    {"id": "b", "title": "图表", "description": "可视化", "author": "alice"},
    {"id": "c", "title": "Settings", "description": "配置", "author": "obox"},
]


def test_empty_query_returns_all() -> None:
    assert filter_apps(APPS, "") == APPS
    assert filter_apps(APPS, "   ") == APPS


def test_title_description_author() -> None:
    assert [app["id"] for app in filter_apps(APPS, "笔")] == ["a"]
    assert [app["id"] for app in filter_apps(APPS, "可视化")] == ["b"]
    assert [app["id"] for app in filter_apps(APPS, "obox")] == ["a", "c"]


def test_case_insensitive() -> None:
    assert [app["id"] for app in filter_apps(APPS, "SETTINGS")] == ["c"]
    assert [app["id"] for app in filter_apps(APPS, "Ali")] == ["b"]


def test_no_match() -> None:
    assert filter_apps(APPS, "zzz") == []
