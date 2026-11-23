"""extension.json 的模型与校验。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..api.errors import ManifestError

_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_ALLOWED_CONTRIBUTES = {"commands", "views", "viewsContainers", "configuration", "app"}
_APP_ID = re.compile(r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$")
_REQUIRED = ("name", "version", "publisher", "description", "main", "icon")


@dataclass(frozen=True)
class Manifest:
    """一份合法的扩展清单。"""

    name: str
    version: str
    publisher: str
    description: str
    main: str
    icon: str
    activation_events: tuple[str, ...]
    contributes: dict[str, Any]
    directory: Path

    @property
    def extension_id(self) -> str:
        return f"{self.name}.{self.publisher}"

    @property
    def configuration(self) -> dict[str, dict[str, Any]]:
        configuration = self.contributes.get("configuration") or {}
        return configuration.get("properties") or {}

    @property
    def apps(self) -> list[dict[str, Any]]:
        """contributes.app 归一化成应用清单；icon 解析成绝对路径。"""
        raw = self.contributes.get("app")
        if raw is None:
            return []
        items = raw if isinstance(raw, list) else [raw]
        result: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            data = item if isinstance(item, dict) else {}
            default = f"{self.extension_id}.app" if len(items) == 1 else f"{self.extension_id}.app{index}"
            app_id = str(data.get("id") or default)
            icon_path = self.icon_path
            icon = str(data.get("icon") or "")
            if icon:
                candidate = (self.assets_dir / icon).resolve()
                if self.assets_dir.resolve() in candidate.parents and candidate.is_file():
                    icon_path = candidate
            result.append(
                {
                    "id": app_id,
                    "title": str(data.get("title") or self.description or self.name),
                    "icon": str(icon_path),
                    "single": bool(data.get("single", True)),
                    "persistent": bool(data.get("persistent", False)),
                }
            )
        return result

    @property
    def app_id(self) -> str:
        """声明了 contributes.app 才返回 id，缺省是 {扩展标识}.app。"""
        app = self.contributes.get("app")
        if app is None:
            return ""
        if isinstance(app, dict):
            return str(app.get("id") or f"{self.extension_id}.app")
        return f"{self.extension_id}.app"

    @property
    def app_title(self) -> str:
        app = self.contributes.get("app")
        if isinstance(app, dict) and app.get("title"):
            return str(app["title"])
        return self.description or self.name

    @property
    def assets_dir(self) -> Path:
        return self.directory / "assets"

    @property
    def icon_path(self) -> Path:
        return self.assets_dir / self.icon


def load_manifest(directory: Path) -> Manifest:
    """读取并校验清单；任何不合规都抛 ManifestError。"""
    raw = _read_manifest(directory)
    name, publisher = _validate_identity(raw)
    return Manifest(
        name=name,
        version=str(raw["version"]),
        publisher=publisher,
        description=str(raw["description"]),
        main=_validate_entry(directory, raw),
        icon=_validate_icon(directory, raw),
        activation_events=_validate_events(raw),
        contributes=_validate_contributes(raw),
        directory=directory,
    )


def _read_manifest(directory: Path) -> dict[str, Any]:
    manifest_path = directory / "extension.json"
    if not manifest_path.exists():
        raise ManifestError(f"缺少 extension.json：{directory}")
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"extension.json 不是合法 JSON：{exc}") from exc
    if not isinstance(raw, dict):
        raise ManifestError("extension.json 顶层必须是对象")
    missing = [key for key in _REQUIRED if not raw.get(key)]
    if missing:
        raise ManifestError(f"清单缺少字段：{', '.join(missing)}")
    return raw


def _validate_identity(raw: dict[str, Any]) -> tuple[str, str]:
    name = str(raw["name"])
    publisher = str(raw["publisher"])
    if not _NAME_PATTERN.match(name):
        raise ManifestError(f"name 只能是小写字母、数字与连字符：{name}")
    if not _NAME_PATTERN.match(publisher):
        raise ManifestError(f"publisher 只能是小写字母、数字与连字符：{publisher}")
    return name, publisher


def _validate_entry(directory: Path, raw: dict[str, Any]) -> str:
    main = str(raw["main"])
    if main != "extension.py":
        raise ManifestError(f"入口固定为 extension.py，实际是 {main}")
    if not (directory / main).exists() and not (directory / "extension.pyd").exists():
        raise ManifestError("入口文件不存在：extension.py 与 extension.pyd 都没有")
    return main


def _validate_icon(directory: Path, raw: dict[str, Any]) -> str:
    icon = str(raw["icon"])
    if not icon.lower().endswith(".svg"):
        raise ManifestError(f"图标必须是 svg：{icon}")
    assets = (directory / "assets").resolve()
    icon_path = (assets / icon).resolve()
    if assets not in icon_path.parents:
        raise ManifestError(f"图标路径越出 assets：{icon}")
    return icon


def _validate_contributes(raw: dict[str, Any]) -> dict[str, Any]:
    contributes = raw.get("contributes") or {}
    if not isinstance(contributes, dict):
        raise ManifestError("contributes 必须是对象")
    if "app" in contributes and contributes["app"] is None:
        contributes.pop("app", None)
    if "app" in contributes:
        app = contributes["app"]
        items = app if isinstance(app, list) else [app]
        seen: set[str] = set()
        for item in items:
            if item is True:
                continue
            if not isinstance(item, dict):
                raise ManifestError("contributes.app 的每一项必须是对象或 true")
            app_id = item.get("id")
            if app_id is not None:
                if not _APP_ID.match(str(app_id)):
                    raise ManifestError(f"app id 不合法：{app_id}")
                if str(app_id) in seen:
                    raise ManifestError(f"app id 重复：{app_id}")
                seen.add(str(app_id))
            for flag in ("single", "persistent"):
                if flag in item and not isinstance(item[flag], bool):
                    raise ManifestError(f"contributes.app 的 {flag} 必须是布尔值")
            if "icon" in item and not isinstance(item["icon"], str):
                raise ManifestError("contributes.app 的 icon 必须是字符串")
    views = contributes.get("views") or []
    if not isinstance(views, list):
        raise ManifestError("contributes.views 必须是数组")
    for view in views:
        if not isinstance(view, dict):
            raise ManifestError("contributes.views 的每一项必须是对象")
        container = str(view.get("container") or "sidebar")
        if container not in ("sidebar", "bottom"):
            raise ManifestError(f"视图容器只能是 sidebar 或 bottom，实际是 {container}")
        view["container"] = container
    if "configuration" in contributes:
        _validate_configuration(contributes["configuration"])
    unknown = set(contributes) - _ALLOWED_CONTRIBUTES
    if unknown:
        raise ManifestError(f"不支持的注册点：{', '.join(sorted(unknown))}")
    return contributes


def _validate_configuration(configuration: Any) -> None:
    if not isinstance(configuration, dict):
        raise ManifestError("contributes.configuration 必须是对象")
    properties = configuration.get("properties")
    if not isinstance(properties, dict) or not properties:
        raise ManifestError("contributes.configuration.properties 必须是非空对象")
    for key, spec in properties.items():
        if not re.match(r"^[a-z][a-z0-9]*$", str(key)):
            raise ManifestError(f"配置键不合法：{key}")
        if not isinstance(spec, dict):
            raise ManifestError(f"配置项 {key} 必须是对象")
        kind = spec.get("type")
        if kind not in ("bool", "string", "enum"):
            raise ManifestError(f"配置项 {key} 的 type 只能是 bool、string 或 enum")
        if not spec.get("title"):
            raise ManifestError(f"配置项 {key} 缺少 title")
        if kind == "enum":
            values = spec.get("enum")
            if not isinstance(values, list) or not values:
                raise ManifestError(f"配置项 {key} 的 enum 必须是非空数组")
            default = spec.get("default")
            if default is not None and default not in values:
                raise ManifestError(f"配置项 {key} 的默认值不在 enum 里")


def _validate_events(raw: dict[str, Any]) -> tuple[str, ...]:
    events = raw.get("activationEvents") or []
    if not isinstance(events, list) or not all(isinstance(item, str) for item in events):
        raise ManifestError("activationEvents 必须是字符串数组")
    return tuple(events)
