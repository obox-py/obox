"""设置里的只读条目。"""

from __future__ import annotations

from pathlib import Path

import pytest
from obox.qt import Qt

from obox.api.errors import ComponentNotFound
from obox.app import OboxApp
from obox.ui.builder import Builder
from obox.ui.parser import parse_fragment
from obox.ui.registry import ComponentRegistry
from tests.fake_provider import build_provider

ROOT = Path(__file__).resolve().parent.parent


def test_version_item_is_label(qapp, tmp_path) -> None:
    obox = OboxApp(ROOT, language="zh-CN", data_dir=str(tmp_path))
    groups = {group["id"]: group for group in obox._settings_groups()}
    item = groups["about"]["items"][0]
    assert item["type"] == "label"
    assert item["value"]
    obox.shutdown()


def test_settings_renders_label_as_text(qapp) -> None:
    source = (ROOT / "extensions/settings/views/main.oml").read_text(encoding="utf-8")
    provider = build_provider()
    registry = ComponentRegistry()
    data = {
        "groups": [{"id": "about", "title": "关于", "selected": "true"}],
        "items": [
            {
                "key": "obox.version",
                "title": "版本",
                "description": "",
                "type": "label",
                "value": "0.1.0",
            }
        ],
        "currentTitle": "关于",
    }
    builder = Builder("settings.obox", registry, provider.component_types, data=data)
    root = builder.build(parse_fragment(source))
    assert root is not None
    label = registry.lookup("settings.obox", "item-label-obox.version")
    assert label.text() == "0.1.0"
    assert label.widget.focusPolicy() == Qt.FocusPolicy.NoFocus
    with pytest.raises(ComponentNotFound):
        registry.lookup("settings.obox", "item-string-obox.version")