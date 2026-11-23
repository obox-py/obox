"""i18n.json 解析：三种写法与 id 校验。"""

from __future__ import annotations

import pytest

from obox.i18n import I18nError, is_valid_id, parse_document


def test_array_form() -> None:
    entries = parse_document(
        [
            {"id": "title", "lang": "zh-CN", "value": "示范"},
            {"id": "title", "lang": "en-US", "value": "Demo"},
            {"id": "dialog.ok", "lang": "zh-CN", "value": "好"},
        ]
    )
    assert entries["title"] == {"zh-CN": "示范", "en-US": "Demo"}
    assert entries["dialog.ok"] == {"zh-CN": "好"}


def test_id_to_list_form() -> None:
    entries = parse_document({"title": [{"lang": "zh-CN", "value": "示范"}]})
    assert entries["title"]["zh-CN"] == "示范"


def test_id_to_map_form() -> None:
    entries = parse_document({"title": {"zh-CN": "示范", "en-US": "Demo"}})
    assert entries["title"]["en-US"] == "Demo"


def test_invalid_ids() -> None:
    for bad in ("Title", "1abc", "a..b", "a.B", "a-b"):
        assert not is_valid_id(bad)
        with pytest.raises(I18nError):
            parse_document([{"id": bad, "lang": "zh-CN", "value": "x"}])
    for good in ("title", "dialog.ok", "a1.b2"):
        assert is_valid_id(good)


def test_missing_zh_cn() -> None:
    with pytest.raises(I18nError):
        parse_document({"title": {"en-US": "Demo"}})
    with pytest.raises(I18nError):
        parse_document([{"id": "title", "lang": "en-US", "value": "Demo"}])


def test_bad_shape() -> None:
    with pytest.raises(I18nError):
        parse_document("nope")
    with pytest.raises(I18nError):
        parse_document([{"id": "title", "value": "x"}])
