"""i18n 注册与占位符替换。"""

from __future__ import annotations

import pytest

from obox.i18n import DEFAULT_LANGUAGE, I18nError, I18nRegistry


def test_register_and_translate(qapp=None) -> None:
    registry = I18nRegistry()
    registry.register("demo.obox", "title", {"zh-CN": "示范", "en-US": "Demo"})
    assert registry.translate("{{i18n.title}}", "demo.obox") == "示范"
    registry.set_language("en-US")
    assert registry.translate("前缀 {{i18n.title}} 后缀", "demo.obox") == "前缀 Demo 后缀"


def test_missing_language_falls_back_to_zh(qapp=None) -> None:
    registry = I18nRegistry(language="fr-FR")
    registry.register("demo.obox", "title", {"zh-CN": "示范", "en-US": "Demo"})
    assert registry.resolve("demo.obox", "title") == "示范"


def test_zh_cn_required(qapp=None) -> None:
    registry = I18nRegistry()
    with pytest.raises(I18nError):
        registry.register("demo.obox", "title", {"en-US": "Demo"})
    with pytest.raises(I18nError):
        registry.register("demo.obox", "title", {})


def test_scope_isolation(qapp=None) -> None:
    registry = I18nRegistry()
    registry.register("a.one", "title", {"zh-CN": "甲"})
    registry.register("b.two", "title", {"zh-CN": "乙"})
    assert registry.translate("{{i18n.title}}", "a.one") == "甲"
    assert registry.translate("{{i18n.title}}", "b.two") == "乙"


def test_unknown_placeholder_kept(qapp=None) -> None:
    registry = I18nRegistry()
    assert registry.translate("{{i18n.nope}}", "demo.obox") == "{{i18n.nope}}"


def test_default_language_constant() -> None:
    assert DEFAULT_LANGUAGE == "zh-CN"
