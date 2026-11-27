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

def test_supported_languages_are_the_four_codes() -> None:
    from obox.i18n import SUPPORTED_LANGUAGES

    assert SUPPORTED_LANGUAGES == ("zh-CN", "zh-HK", "zh-TW", "en-US")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("zh-CN", "zh-CN"),
        ("zh_hk", "zh-HK"),
        ("en-US", "en-US"),
        ("中国大陆", "zh-CN"),
        ("中国香港", "zh-HK"),
        ("中国台湾", "zh-TW"),
        ("America", "en-US"),
        ("fr-FR", ""),
        ("", ""),
    ],
)
def test_normalize_language(value: str, expected: str) -> None:
    from obox.i18n import normalize_language

    assert normalize_language(value) == expected


def test_every_bundle_covers_four_languages() -> None:
    """九份 i18n.json 都要四种语言齐全，且 id 合法。"""
    import json
    from pathlib import Path

    from obox.i18n import SUPPORTED_LANGUAGES, is_valid_id, parse_document

    root = Path(__file__).resolve().parent.parent
    bundles = [root / "obox" / "i18n.json", *sorted((root / "extensions").glob("*/i18n.json"))]
    # 仓里只有 obox 与系统扩展（app/settings/management），用户扩展在各自仓库、不入主仓
    assert len(bundles) >= 4
    for path in bundles:
        entries = parse_document(json.loads(path.read_text(encoding="utf-8")), str(path))
        for entry_id, values in entries.items():
            assert is_valid_id(entry_id), f"{path.name}: 非法 id {entry_id}"
            missing = [code for code in SUPPORTED_LANGUAGES if code not in values]
            assert not missing, f"{path.name}: {entry_id} 缺 {missing}"
