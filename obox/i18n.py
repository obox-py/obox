"""i18n 注册表：按 name 与 id 保存多语言文案，渲染前替换 {{i18n.<id>}}。"""

from __future__ import annotations

import re

DEFAULT_LANGUAGE = "zh-CN"
BASE_DEFAULTS = {"zh": "zh-CN", "en": "en-US"}
_PLACEHOLDER = re.compile(r"\{\{i18n\.([A-Za-z0-9_.-]+)\}\}")
_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$")


class I18nError(Exception):
    """注册或解析失败。"""


def is_valid_id(entry_id: str) -> bool:
    """id 形如 title、dialog.ok：小写字母开头，段内小写字母与数字，点分段。"""
    return bool(_ID_PATTERN.match(entry_id or ""))


def parse_document(data: object, source: str = "") -> dict[str, dict[str, str]]:
    """把 i18n.json 解析成 id -> {lang: value}。

    接受三种写法：数组 [{id, lang, value}]、id -> [{lang, value}]、id -> {lang: value}。
    """
    origin = f"（{source}）" if source else ""
    entries: dict[str, dict[str, str]] = {}

    def add(entry_id: str, lang: str, value: str) -> None:
        if not is_valid_id(entry_id):
            raise I18nError(f"非法 i18n id{origin}：{entry_id!r}，要求小写字母开头、可含数字与点")
        if not lang:
            raise I18nError(f"{entry_id} 的 lang 不能为空{origin}")
        entries.setdefault(entry_id, {})[lang] = str(value)

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict) or not {"id", "lang", "value"} <= set(item):
                raise I18nError(f"数组项必须是 {{id, lang, value}}{origin}")
            add(str(item["id"]), str(item["lang"]), str(item["value"]))
    elif isinstance(data, dict):
        for entry_id, payload in data.items():
            if isinstance(payload, list):
                for item in payload:
                    if not isinstance(item, dict) or not {"lang", "value"} <= set(item):
                        raise I18nError(f"{entry_id} 的项必须是 {{lang, value}}{origin}")
                    add(str(entry_id), str(item["lang"]), str(item["value"]))
            elif isinstance(payload, dict):
                for lang, value in payload.items():
                    add(str(entry_id), str(lang), str(value))
            else:
                raise I18nError(f"{entry_id} 的值必须是数组或对象{origin}")
    else:
        raise I18nError(f"i18n.json 必须是数组或对象{origin}")

    missing = [entry_id for entry_id, values in entries.items() if DEFAULT_LANGUAGE not in values]
    if missing:
        raise I18nError(f"缺少 {DEFAULT_LANGUAGE}：{', '.join(sorted(missing))}{origin}")
    return entries


class I18nRegistry:
    """name 是扩展标识（obox 主窗体用 obox），id 是条目 id，values 是 BCP-47 到文案。"""

    def __init__(self, language: str = DEFAULT_LANGUAGE) -> None:
        self._language = language or DEFAULT_LANGUAGE
        self._entries: dict[tuple[str, str], dict[str, str]] = {}

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, code: str) -> None:
        self._language = code or DEFAULT_LANGUAGE

    def register(self, name: str, entry_id: str, values: dict[str, str]) -> None:
        if not name or not entry_id:
            raise I18nError("name 与 id 都不能为空")
        if not isinstance(values, dict) or not values:
            raise I18nError(f"{name}.{entry_id} 的 values 必须是非空字典")
        normalized = {str(key): str(value) for key, value in values.items()}
        if DEFAULT_LANGUAGE not in normalized:
            raise I18nError(f"{name}.{entry_id} 必须提供 {DEFAULT_LANGUAGE}")
        self._entries[(name, entry_id)] = normalized

    def unregister(self, name: str) -> None:
        for key in [key for key in self._entries if key[0] == name]:
            self._entries.pop(key, None)

    def languages(self) -> list[str]:
        codes = {DEFAULT_LANGUAGE}
        for values in self._entries.values():
            codes.update(values)
        return sorted(codes)

    def ids(self, name: str) -> list[str]:
        return sorted(entry_id for owner, entry_id in self._entries if owner == name)

    def _candidates(self) -> list[str]:
        """当前语言 → 语言基码 → 基码缺省 → zh-CN，去重保序。"""
        language = self._language or DEFAULT_LANGUAGE
        base = language.split("-")[0].lower()
        order = [language]
        if base:
            order.append(base)
            preferred = BASE_DEFAULTS.get(base)
            if preferred:
                order.append(preferred)
        order.append(DEFAULT_LANGUAGE)
        seen: list[str] = []
        for code in order:
            if code and code not in seen:
                seen.append(code)
        return seen

    def resolve(self, name: str, entry_id: str) -> str | None:
        values = self._entries.get((name, entry_id))
        if values is None:
            return None
        for code in self._candidates():
            if code in values:
                return values[code]
        return values.get(DEFAULT_LANGUAGE)

    def translate(self, text: str, name: str) -> str:
        def replace(match: re.Match[str]) -> str:
            value = self.resolve(name, match.group(1))
            return value if value is not None else match.group(0)

        return _PLACEHOLDER.sub(replace, text)
