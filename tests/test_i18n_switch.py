"""i18n 语言列表与切换。"""

from __future__ import annotations

from obox.i18n import I18nRegistry


def test_languages_union(qapp=None) -> None:
    registry = I18nRegistry()
    registry.register("a.one", "t", {"zh-CN": "甲", "en-US": "A"})
    registry.register("b.two", "t", {"zh-CN": "乙"})
    assert registry.languages() == ["en-US", "zh-CN"]


def test_switch_changes_resolution(qapp=None) -> None:
    registry = I18nRegistry()
    registry.register("a.one", "t", {"zh-CN": "甲", "en-US": "A"})
    assert registry.translate("x", "a.one") == "x"
    registry.set_language("en-US")
    assert registry.resolve("a.one", "t") == "A"

def test_region_falls_back_to_language_default(qapp=None) -> None:
    registry = I18nRegistry("zh-HK")
    registry.register("a.one", "t", {"zh-CN": "甲", "en-US": "A"})
    assert registry.resolve("a.one", "t") == "甲"

    registry.set_language("zh-TW")
    assert registry.resolve("a.one", "t") == "甲"

    registry.set_language("en-GB")
    assert registry.resolve("a.one", "t") == "A"

    registry.set_language("fr-FR")
    assert registry.resolve("a.one", "t") == "甲"


def test_exact_region_wins_over_fallback(qapp=None) -> None:
    registry = I18nRegistry("zh-HK")
    registry.register("a.one", "t", {"zh-CN": "甲", "zh-HK": "甲港"})
    assert registry.resolve("a.one", "t") == "甲港"
