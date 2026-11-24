"""应用装配：主题套件、消息总线、扩展宿主与组件装配。"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import QFileSystemWatcher, Qt, QTimer
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QFrame, QScrollArea, QVBoxLayout, QWidget

from .api.component import (
    COMPONENT_EVENT_MSG,
    COMPONENT_MODIFY_MSG,
    COMPONENT_STATE_MSG,
    ComponentModifyMessage,
    ComponentStateMessage,
)
from .api.errors import ComponentNotFound, ForbiddenOwner, OboxError, error_payload
from .api.app import APP_LAUNCH_MSG, APP_LIST_MSG, APP_UI_MSG, APP_VIEW_DATA_MSG, app_open_message
from .api.extensions import (
    EXTENSIONS_CHANGED_MSG,
    EXTENSIONS_MANAGE_MSG,
    EXTENSIONS_RESULT_MSG,
    enable_extension_message,
    extensions_list_message,
    install_extension_message,
    remove_extension_message,
)
from .api.i18n import I18N_REGISTER_MSG, I18nRegisterMessage
from .api.lifecycle import VIEW_MOUNTED_MSG, view_message
from .api.settings import (
    EXTENSION_CONFIG_MSG,
    SETTINGS_SET_MSG,
    extension_config_message,
    settings_list_message,
)
from .api.view import VIEW_DATA_MSG, VIEW_SCROLL_MSG, anchor_changed_message
from .api.message import OB_BOX, Message
from . import __version__
from .i18n import DEFAULT_LANGUAGE, I18nError, I18nRegistry, parse_document
from .runtime import resolve as resolve_paths
from .oml import OmlError, is_oml, load_oml
from .ui.close_action import CLOSE_ACTIONS, decide_close
from .ui import palette
from .ui.anchor import AnchorController
from .ui.close_dialog import CloseDialog
from .ui.confirm_dialog import ConfirmDialog
from .ui.progress_dialog import InstallProgressDialog
from .ui.single_instance import SingleInstance
from .ui.tray import TrayIcon
from .core.bus import MessageBus
from .extensions.supervisor import Supervisor
from .ui.builder import Builder
from .ui.component_protocol import KitContractError
from .ui.components import COMPONENT_TYPES
from .ui.kit import DEFAULT_THEME, KitError, load_provider, scan_themes, select_kit
from .ui.app_window import AppWindow
from .ui.main_window import MainWindow
from .ui.parser import Node, parse_fragment
from .ui.qss import filter_stylesheet
from .ui.registry import ComponentRegistry
from .ui.template import ViewHandle


DEFAULT_VIEW = "app.main"
APP_USER_MODEL_ID = "obox.desktop"


def apply_app_user_model_id() -> None:
    """Windows 任务栏按进程级 AppUserModelID 分组，图标才不会落回 python。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except (AttributeError, OSError) as exc:
        print(f"[obox] AppUserModelID 设置失败：{exc}", file=sys.stderr)


class OboxApp:
    """把各层组装起来；组件消息在这里落地成对 kit 组件的读写。"""

    def __init__(
        self,
        project_root: Path,
        extensions_dir: str = "",
        theme: str = "",
        language: str = "",
        provider: Any = None,
        data_dir: str | Path = "",
    ) -> None:
        self.project_root = project_root
        self.data_dir = Path(data_dir) if data_dir else project_root / ".obox"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.themes_root = project_root / ".theme"
        self.user_themes_root = self.data_dir / "themes"
        if (project_root / "themes").is_dir():
            self.themes_root = project_root / "themes"
        self.config_path = self.data_dir / "config.json"
        self.extensions_root = Path(extensions_dir) if extensions_dir else project_root / "extensions"
        self.theme_name = theme or self._configured_theme() or DEFAULT_THEME
        self._kit_dir: Path | None = None
        self.language = language or self._configured_language() or DEFAULT_LANGUAGE
        self.i18n = I18nRegistry(self.language)
        self._register_shell_i18n()
        self.provider: Any = provider or self._load_kit(self.theme_name)
        self._extension_dirs: dict[str, Path] = {}
        self._view_specs: dict[str, dict[str, Any]] = {}
        self._apps: list[dict[str, Any]] = []
        self._app_windows: dict[str, AppWindow] = {}
        self._app_specs: dict[str, dict[str, Any]] = {}
        self._app_counter = 0
        self._view_handles: dict[str, tuple[str, ViewHandle]] = {}
        self._app_handles: dict[str, tuple[str, ViewHandle]] = {}
        self._anchors: dict[str, tuple[str, AnchorController]] = {}
        self._watcher = None
        self._watch_timer = None
        self._settings: dict[str, Any] = self._stored_settings()
        self.close_action = str(self._settings.get("obox.close_action") or "ask")
        if self.close_action not in CLOSE_ACTIONS:
            self.close_action = "ask"
        self._tray: TrayIcon | None = None
        self._progress_dialog: InstallProgressDialog | None = None
        self._startup_done = False
        self._reloading = False
        self._restore_target = ""
        self._single: SingleInstance | None = None
        self._extensions_config: dict[str, dict[str, Any]] = {}
        self._language_cache: list[tuple[str, str]] | None = None
        self._locale_labels = {
            "zh-CN": "中国大陆",
            "zh-HK": "中国香港",
            "zh-TW": "中国台湾",
            "en-US": "America",
        }
        self._extensions: dict[str, dict[str, Any]] = {}
        self._apps_host: QWidget | None = None
        self.registry = ComponentRegistry()
        self.bus = MessageBus(OB_BOX)
        self.bus.on(COMPONENT_STATE_MSG, self._on_state_query)
        self.bus.on(COMPONENT_MODIFY_MSG, self._on_modify)
        self.bus.on(I18N_REGISTER_MSG, self._on_i18n_register)
        self.bus.on(COMPONENT_EVENT_MSG, self._on_component_event)
        self.bus.on(APP_LAUNCH_MSG, self._on_app_launch)
        self.bus.on(VIEW_SCROLL_MSG, self._on_view_scroll)
        self.bus.on(EXTENSION_CONFIG_MSG, lambda message: None)
        self.bus.on(EXTENSIONS_MANAGE_MSG, self._on_extensions_manage)
        self.bus.on(EXTENSIONS_CHANGED_MSG, self._on_extensions_changed)
        self.bus.on(EXTENSIONS_RESULT_MSG, self._on_extension_result)
        self.bus.on(APP_UI_MSG, self._on_app_ui)
        self.bus.on(APP_VIEW_DATA_MSG, self._on_app_view_data)
        self.bus.on(VIEW_DATA_MSG, self._on_view_data)
        self.bus.on(SETTINGS_SET_MSG, self._on_settings_set)
        self.window = MainWindow(translator=lambda text: self.i18n.translate(text, "obox"))
        self.supervisor = Supervisor(project_root, self.bus, self.extensions_root, data_dir=self.data_dir)
        self.supervisor.extensions_ready.connect(self._on_extensions_ready)
        self.supervisor.state_changed.connect(self._on_host_state)

    def start(self) -> None:
        self._apply_provider(self.provider)
        icon_path = Path(__file__).resolve().parent / "assets" / "obox.svg"
        if icon_path.exists():
            self.window.set_window_icon(str(icon_path))
        self.window.show()
        self.window.close_requested.connect(self._on_close_requested)
        self._sync_disabled_file()
        self.supervisor.start()
        self._watch_extensions()
        self._setup_tray()

    def _configured_theme(self) -> str:
        if not self.config_path.exists():
            return ""
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[obox] 配置读取失败：{exc}", file=sys.stderr)
            return ""
        return str(data.get("theme", ""))

    def _register_shell_i18n(self) -> None:
        """obox 自身文案来自 obox/i18n.json；缺文件时退回内置中文。"""
        path = Path(__file__).resolve().parent / "i18n.json"
        try:
            entries = parse_document(json.loads(path.read_text(encoding="utf-8")), str(path))
        except (OSError, json.JSONDecodeError, I18nError) as exc:
            print(f"[obox] 内置文案加载失败：{exc}", file=sys.stderr)
            entries = {
                "home.hint": {
                    "zh-CN": "左侧是扩展注册的图标，点一个查看它的界面；没加载到扩展时这里保持为空。"
                }
            }
        for entry_id, values in entries.items():
            self.i18n.register("obox", entry_id, values)

    def _configured_language(self) -> str:
        if not self.config_path.exists():
            return ""
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ""
        return str(data.get("language", ""))

    def _save_language(self, code: str) -> None:
        data: dict[str, Any] = {}
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {}
        data["language"] = code
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def switch_language(self, code: str) -> bool:
        """切语言后重建全部视图，文案与界面一起换；重建后回到原视图。"""
        if not code or code == self.i18n.language:
            return False
        current = self.window.current_view_id()
        self.i18n.set_language(code)
        self.language = code
        self._save_language(code)
        for window in list(self._app_windows.values()):
            window.force_close()
        self._app_windows.clear()
        self._app_specs.clear()
        self.window.retranslate()
        self.window.clear_views()
        for owner in {spec["extension_id"] for spec in self._view_specs.values()}:
            self.registry.unregister_owner(owner)
        prepared = [item for spec in self._view_specs.values() if (item := self._mount_view(spec, rebuild=True))]
        self._apply_extension_styles(prepared)
        self._restore_view(current)
        self._push_settings()
        return True

    def _restore_view(self, view_id: str) -> None:
        if view_id and view_id in self.window.view_ids():
            self.window.show_view(view_id)

    def _load_kit(self, name: str):
        kits = scan_themes([self.themes_root, self.user_themes_root])
        if not kits:
            raise KitError(f"{self.themes_root} 下没有可用的主题套件")
        kit = select_kit(kits, name)
        self._kit_dir = kit.directory
        return load_provider(kit)

    def switch_theme(self, name: str) -> bool:
        """换一套界面并重建所有视图；失败时保留当前套件。"""
        try:
            provider = self._load_kit(name)
        except OboxError as exc:
            print(f"[obox] 切换主题失败：{exc}", file=sys.stderr)
            self.window.notify_warning("切换主题失败", str(exc))
            return False
        current = self.window.current_view_id()
        self.provider = provider
        self.theme_name = name
        self._apply_provider(provider)
        self.window.clear_views()
        for owner in {spec["extension_id"] for spec in self._view_specs.values()}:
            self.registry.unregister_owner(owner)
        prepared = [item for spec in self._view_specs.values() if (item := self._mount_view(spec, rebuild=True))]
        self._apply_extension_styles(prepared)
        self._restore_view(current)
        self._push_settings()
        return True

    def _apply_provider(self, provider: Any) -> None:
        """主题跟着套件走：先注册字体、切调色板，再套 QSS。"""
        palette.set_active(getattr(provider, "palette", None))
        self._register_fonts(provider)
        self.window.setStyleSheet(provider.stylesheet)
        self.window.set_icon_colors(
            getattr(provider, "icon_muted", "#6f6b64"),
            getattr(provider, "icon_active", "#5b7f95"),
        )
        self.window.set_title_button_colors(
            getattr(provider, "title_muted", getattr(provider, "icon_muted", "#4e5969")),
            getattr(provider, "title_active", getattr(provider, "icon_active", "#1d2129")),
            getattr(provider, "danger", "#d93026"),
        )
        self._apply_tray_styles()

    def _register_fonts(self, provider: Any) -> None:
        """套件自带的字体文件在运行时注册；family 名由套件 QSS 引用。"""
        candidates = []
        if self._kit_dir is not None:
            candidates.append(self._kit_dir / "fonts")
        declared = getattr(provider, "font_dir", None)
        if declared:
            candidates.append(Path(str(declared)))
        font_dir = next((path for path in candidates if path.is_dir()), None)
        if font_dir is None:
            return
        families: list[str] = []
        for font_file in sorted(font_dir.glob("*.ttf")):
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id >= 0:
                families.extend(QFontDatabase.applicationFontFamilies(font_id))
        application = QApplication.instance()
        if families and application is not None:
            application.setFont(QFont(families[0], 10))

    def _watch_extensions(self) -> None:
        """监听扩展目录；变化后去抖重启宿主，让应用列表与视图同步。"""
        if self._watcher is None:
            self._watcher = QFileSystemWatcher(self.window)
            self._watcher.directoryChanged.connect(self._on_extensions_dir_changed)
            self._watch_timer = QTimer(self.window)
            self._watch_timer.setSingleShot(True)
            self._watch_timer.timeout.connect(self._restart_extensions)
        watched = set(self._watcher.directories())
        for path in (self.extensions_root, self.data_dir / "extensions"):
            if path.is_dir() and str(path) not in watched:
                self._watcher.addPath(str(path))

    def _on_extensions_dir_changed(self, _path: str) -> None:
        if self._watch_timer is not None:
            self._watch_timer.start(400)

    def _restart_extensions(self) -> None:
        self.window.notify_warning("扩展目录变化", "正在重新加载扩展…")
        self.supervisor.restart()

    def _on_host_state(self, state: str, detail: str) -> None:
        print(f"[obox] 宿主状态 {state}：{detail}", file=sys.stderr)
        if state in ("disconnected", "restarting"):
            self.window.notify_warning("扩展宿主", detail)

    def _on_extensions_ready(self, payload: dict[str, Any]) -> None:
        for extension_id, entries in (payload.get("i18n") or {}).items():
            for entry_id, values in entries.items():
                try:
                    self.i18n.register(str(extension_id), str(entry_id), values)
                except I18nError as exc:
                    print(f"[obox] {extension_id}.{entry_id} 注册失败：{exc}", file=sys.stderr)
        failed = [item for item in payload.get("extensions", []) if item.get("status") != "active"]
        for item in failed:
            print(f"[obox] 扩展 {item.get('id')} 未激活：{item.get('error')}", file=sys.stderr)
        if failed:
            names = "、".join(str(item.get("id")) for item in failed)
            self.window.notify_warning("扩展未激活", names)
        for item in payload.get("extensions", []):
            self._extensions[str(item.get("id"))] = dict(item)
            directory = str(item.get("directory") or "")
            if directory:
                self._extension_dirs.setdefault(str(item.get("id")), Path(directory))
        self._rebuild_apps()
        self._extensions_config = {
            str(item.get("id")): dict(item.get("configuration") or {})
            for item in payload.get("extensions", [])
            if item.get("status") == "active"
        }
        self._push_apps_list()
        self._push_settings()
        self._push_extension_configs()
        for view in payload.get("views", []):
            self._view_specs[str(view["view_id"])] = dict(view)
            directory = view.get("directory")
            if directory:
                self._extension_dirs.setdefault(str(view["extension_id"]), Path(str(directory)))
        prepared: list[tuple[dict[str, Any], QWidget, list[str]]] = []
        for view in list(self._view_specs.values()):
            if str(view["view_id"]) in self.window.view_ids():
                continue  # 宿主重启后沿用已装配的视图，避免 id 冲突
            item = self._mount_view(view)
            if item is not None:
                prepared.append(item)
        self._apply_extension_styles(prepared)
        self._push_extensions_list()
        if self._reloading:
            self._finish_reload()
        elif not self._startup_done:
            self._startup_done = True
            if DEFAULT_VIEW in self.window.view_ids():
                self.window.show_view(DEFAULT_VIEW)
        self._push_settings()

    def _rebuild_apps(self) -> None:
        """从当前扩展描述重建应用列表；扩展增删后调用。"""
        apps: list[dict[str, Any]] = []
        for item in self._extensions.values():
            if item.get("status") != "active":
                continue
            for app in item.get("apps") or []:
                apps.append(
                    {
                        **app,
                        "extension_id": item.get("id"),
                        "publisher": item.get("publisher", ""),
                        "version": item.get("version", ""),
                        "meta": f"{item.get('publisher', '')} · {item.get('version', '')}",
                        "description": item.get("description", ""),
                    }
                )
        self._apps = apps

    def _mount_view(
        self, view: dict[str, Any], rebuild: bool = False
    ) -> tuple[dict[str, Any], QWidget, list[str]] | None:
        owner = str(view["extension_id"])
        source = str(view["html"])
        if is_oml(source):
            directory = self._extension_dirs.get(owner) or Path(str(view.get("directory", "")))
            try:
                source = load_oml(directory, source)
            except OmlError as exc:
                print(f"[obox] 视图 {view.get('view_id')} 读取失败：{exc}", file=sys.stderr)
                self.window.notify_warning("视图加载失败", str(exc))
                return None
        source = self.i18n.translate(source, owner)
        handle_out: dict[str, Any] = {}
        try:
            root, ids = self.assemble_view(owner, source, data=view.get("data") or {}, handle_out=handle_out)
        except OboxError as exc:
            print(f"[obox] 视图 {view.get('view_id')} 装配失败：{exc}", file=sys.stderr)
            return None
        container = str(view.get("container", "sidebar"))
        if container == "bottom":
            root.setObjectName("obox-bottom-view")
        else:
            sections_root = self._view_root_widget(owner, source)
            sticky = self._take_sticky(sections_root, source)
            scroll = QScrollArea()
            scroll.setObjectName("obox-view-scroll")
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setStyleSheet(
                "#obox-view-scroll { background: transparent; }"
                " QScrollArea > QWidget > QWidget { background: transparent; }"
            )
            scroll.setWidget(root)
            controller = AnchorController(
                scroll, root, parent=scroll, sections_root=sections_root
            )
            controller.anchor_changed.connect(
                lambda anchor, vid=str(view["view_id"]), who=owner: self._send_anchor_changed(
                    vid, anchor, who
                )
            )
            self._anchors[str(view["view_id"])] = (owner, controller)
            if sticky is not None:
                wrapper = QWidget()
                wrapper.setObjectName("obox-view-with-sticky")
                wrapper_layout = QVBoxLayout(wrapper)
                wrapper_layout.setContentsMargins(0, 0, 0, 0)
                wrapper_layout.setSpacing(0)
                sticky.setParent(wrapper)
                wrapper_layout.addWidget(sticky)
                wrapper_layout.addWidget(scroll, 1)
                root = wrapper
            else:
                root = scroll
        self.window.add_view(
            str(view["view_id"]),
            str(view.get("title") or owner),
            root,
            container,
            str(view.get("icon_path", "")),
        )
        handle = handle_out.get("handle")
        if handle is not None:
            self._view_handles[str(view["view_id"])] = (owner, handle)
            if owner == "app.obox":
                try:
                    handle.set_data({"apps": self._apps_payload()})
                except Exception as exc:  # 注入失败不能连累其它视图
                    print(f"[obox] 应用数据注入失败：{exc}", file=sys.stderr)
        self.bus.send(view_message(VIEW_MOUNTED_MSG, owner, str(view["view_id"])))
        return view, root, ids

    def _view_root_widget(self, owner: str, source: str) -> QWidget | None:
        """视图根节点的组件控件；片段没有可解析的根时返回 None。"""
        try:
            nodes = parse_fragment(source)
        except Exception:
            return None
        if not nodes:
            return None
        component_id = nodes[0].component_id or ""
        try:
            component = self.registry.lookup(owner, component_id)
        except OboxError:
            return None
        return component.widget

    def _take_sticky(self, container: QWidget | None, source: str) -> QWidget | None:
        """把视图根第一个声明 sticky 的直接子组件从布局取出，交给调用方放到滚动区上方。"""
        if container is None:
            return None
        try:
            nodes = parse_fragment(source)
        except Exception:
            return None
        if not nodes:
            return None
        view_root = nodes[0]
        layout = container.layout()
        if layout is None:
            return None
        index = 0
        for node in view_root.children:
            if not isinstance(node, Node):
                continue
            if str(node.attrs.get("sticky", "")).lower() == "true":
                if index >= layout.count():
                    return None
                item = layout.itemAt(index)
                widget = item.widget() if item is not None else None
                if widget is None:
                    return None
                layout.removeWidget(widget)
                widget.setParent(None)
                return widget
            index += 1
        return None

    def _send_anchor_changed(self, view_id: str, anchor: str, owner: str) -> None:
        if not anchor:
            return
        self.bus.send(anchor_changed_message(view_id, anchor, owner))

    def _on_view_scroll(self, message: Any) -> None:
        payload = message.payload or {}
        view_id = str(payload.get("view_id") or "")
        entry = self._anchors.get(view_id)
        if entry is None:
            return
        _owner, controller = entry
        offset = payload.get("offset")
        duration = payload.get("duration")
        controller.scroll_to(
            str(payload.get("anchor") or ""),
            64 if offset is None else int(offset),
            600 if duration is None else int(duration),
        )

    def assemble_view(
        self,
        owner: str,
        html_source: str,
        data: dict[str, Any] | None = None,
        handle_out: dict[str, Any] | None = None,
    ) -> tuple[QWidget, list[str]]:
        """把片段装配成控件树；返回根控件与它创建的组件 id。"""
        nodes = parse_fragment(html_source)
        if self.provider is None:
            raise KitContractError("尚未加载主题套件")
        builder = Builder(
            owner,
            self.registry,
            COMPONENT_TYPES,
            self._send_component_event,
            getattr(self.provider, "spacing", None),
            data=data,
        )
        root = builder.build(nodes)
        if handle_out is not None:
            handle = ViewHandle(builder, root, data or {})
            handle.attach(builder.bindings, builder.regions)
            handle_out["handle"] = handle
        return root, builder.created_ids

    def _apply_extension_styles(
        self, prepared: list[tuple[dict[str, Any], QWidget, list[str]]]
    ) -> None:
        """按扩展汇总所有视图的组件 id，再统一下发样式，避免同扩展视图互相误判。"""
        by_owner: dict[str, list[tuple[QWidget, set[str]]]] = {}
        for view, root, ids in prepared:
            by_owner.setdefault(str(view["extension_id"]), []).append((root, set(ids)))
        for owner, entries in by_owner.items():
            style_path = self._style_path(owner)
            if style_path is None:
                continue
            allowed: set[str] = set()
            for _, ids in entries:
                allowed |= ids
            try:
                source = style_path.read_text(encoding="utf-8")
            except OSError as exc:
                print(f"[obox] 样式读取失败 {style_path}：{exc}", file=sys.stderr)
                continue
            stylesheet, rejected = filter_stylesheet(source, allowed)
            if stylesheet:
                for root, _ in entries:
                    root.setStyleSheet(stylesheet)
            for selector in rejected:
                print(f"[obox] 扩展 {owner} 的样式被拒：{selector}", file=sys.stderr)

    def _send_component_event(self, message: Any) -> None:
        try:
            self.bus.send(message)
        except Exception as exc:  # 宿主不在线时界面不能跟着崩
            print(f"[obox] 组件事件发送失败：{exc}", file=sys.stderr)

    def _style_path(self, owner: str) -> Path | None:
        directory = self._extension_dirs.get(owner)
        if directory is None:
            return None
        candidate = directory / "assets" / "style.qss"
        return candidate if candidate.exists() else None

    def _accessor(self, component: Any, state_type: str, index: int) -> str:
        accessors = getattr(component, "state_accessors", {})
        pair = accessors.get(state_type)
        if pair is None:
            raise KitContractError(f"组件 {component.id} 不支持状态 {state_type}")
        return pair[index]

    def _on_state_query(self, message: ComponentStateMessage) -> None:
        try:
            component = self.registry.lookup(message.src, message.id)
            value = getattr(component, self._accessor(component, message.state_type, 0))()
        except OboxError as exc:
            self._reply_error(message, exc)
            return
        if message.correlation_id:
            self.bus.reply(message, {"value": value})

    def _on_modify(self, message: ComponentModifyMessage) -> None:
        try:
            component = self._owned_component(message.src, message.id)
            getattr(component, self._accessor(component, message.state_type, 1))(message.value)
        except OboxError as exc:
            self._reply_error(message, exc)
            return
        if message.correlation_id:
            self.bus.reply(message, {"ok": True})

    def _on_i18n_register(self, message: I18nRegisterMessage) -> None:
        payload = message.payload or {}
        name = str(payload.get("name") or message.src)
        try:
            if name != message.src:
                raise I18nError("扩展只能注册自己的 i18n")
            self.i18n.register(name, str(payload.get("id")), payload.get("values") or {})
        except I18nError as exc:
            print(f"[obox] i18n 注册失败：{exc}", file=sys.stderr)
            if message.correlation_id:
                self.bus.reply(message, {"ok": False, "error": str(exc)})
            return
        if message.correlation_id:
            self.bus.reply(message, {"ok": True})

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save_config(self, data: dict[str, Any]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _stored_settings(self) -> dict[str, Any]:
        return dict(self._load_config().get("settings") or {})

    def _save_settings(self) -> None:
        data = self._load_config()
        settings = dict(data.get("settings") or {})
        settings.update(self._settings)
        data["settings"] = settings
        if "obox.theme" in settings:
            data["theme"] = settings["obox.theme"]
        if "obox.language" in settings:
            data["language"] = settings["obox.language"]
        self._save_config(data)

    def _t(self, key: str) -> str:
        return self.i18n.translate("{{i18n." + key + "}}", "obox")

    def language_options(self) -> list[tuple[str, str]]:
        """全部地区：Qt 能枚举的 locale + 已注册语言，标签用原生地区名。"""
        if self._language_cache is not None:
            return list(self._language_cache)
        from PySide6.QtCore import QLocale

        items: dict[str, str] = {}
        used: dict[str, str] = {}
        locales = QLocale.matchingLocales(
            QLocale.Language.AnyLanguage,
            QLocale.Script.AnyScript,
            QLocale.Country.AnyCountry,
        )
        for locale in locales:
            code = locale.name().replace("_", "-")
            if not code or code == "C":
                continue
            label = self._locale_labels.get(code) or (
                locale.nativeTerritoryName() or locale.nativeLanguageName() or code
            )
            label = label.replace(",", "·").strip() or code
            if label in used and used[label] != code:
                label = f"{label}（{code}）"
            used.setdefault(label, code)
            items.setdefault(code, label)
        for code in self.i18n.languages():
            if code in items:
                continue
            label = self._locale_labels.get(code, code)
            items[code] = label
            used.setdefault(label, code)
        result = sorted(items.items(), key=lambda item: item[1])
        self._language_cache = result
        return list(result)

    def language_label(self, code: str) -> str:
        for candidate, label in self.language_options():
            if candidate == code:
                return label
        return code

    def _language_code(self, value: str) -> str:
        for code, label in self.language_options():
            if label == value:
                return code
        return value if value in self.i18n.languages() else ""

    def _settings_groups(self) -> list[dict[str, Any]]:
        groups: list[dict[str, Any]] = [
            {
                "id": "behavior",
                "title": self._t("settings.group.behavior"),
                "items": [
                    {
                        "key": "obox.close_action",
                        "title": self._t("settings.item.closeaction"),
                        "type": "enum",
                        "value": self.close_action,
                        "options": "ask,tray,quit",
                        "description": self._t("settings.item.closeaction.desc"),
                    }
                ],
            },
            {
                "id": "appearance",
                "title": self._t("settings.group.appearance"),
                "items": [
                    {
                        "key": "obox.theme",
                        "title": self._t("settings.item.theme"),
                        "type": "enum",
                        "value": self.theme_name,
                        "enum": ["light", "dark"],
                        "options": "light,dark",
                        "description": self._t("settings.item.theme.desc"),
                    }
                ],
            },
            {
                "id": "language",
                "title": self._t("settings.group.language"),
                "items": [
                    {
                        "key": "obox.language",
                        "title": self._t("settings.item.language"),
                        "type": "enum",
                        "value": self.language_label(self.i18n.language),
                        "enum": [label for _code, label in self.language_options()],
                        "options": ",".join(label for _code, label in self.language_options()),
                        "description": self._t("settings.item.language.desc"),
                    }
                ],
            },
        ]
        extension_items: list[dict[str, Any]] = []
        for extension_id, properties in self._extensions_config.items():
            for name, spec in properties.items():
                key = f"{extension_id}.{name}"
                value = self._settings.get(key, spec.get("default", ""))
                item: dict[str, Any] = {
                    "key": key,
                    "title": str(spec.get("title", name)),
                    "type": str(spec.get("type", "string")),
                    "value": value,
                    "description": str(spec.get("description", "")),
                }
                if item["type"] == "bool":
                    item["checked"] = "true" if bool(value) else "false"
                elif item["type"] == "enum":
                    options = list(spec.get("enum") or [])
                    item["enum"] = options
                    item["options"] = ",".join(str(option) for option in options)
                extension_items.append(item)
        groups.append({"id": "extensions", "title": self._t("settings.group.extensions"), "items": extension_items})
        groups.append(
            {
                "id": "about",
                "title": self._t("settings.group.about"),
                "items": [
                    {
                        "key": "obox.version",
                        "title": self._t("settings.item.version"),
                        "type": "label",
                        "value": __version__,
                    }
                ],
            }
        )
        return groups

    def _push_extension_configs(self) -> None:
        """把每个扩展自己的配置值推给它：激活后一次，设置变更后再推。"""
        for extension_id, properties in self._extensions_config.items():
            values: dict[str, Any] = {}
            defaults: dict[str, Any] = {}
            for name, spec in properties.items():
                spec = spec if isinstance(spec, dict) else {}
                default = spec.get("default")
                defaults[name] = default
                values[name] = self._settings.get(f"{extension_id}.{name}", default)
            try:
                self.bus.send(
                    extension_config_message(OB_BOX, extension_id, values, defaults)
                )
            except Exception as exc:
                print(f"[obox] 配置下发失败 {extension_id}：{exc}", file=sys.stderr)

    def _push_settings(self) -> None:
        self.bus.send(settings_list_message(self._settings_groups()))

    def _setting_spec(self, key: str) -> dict[str, Any] | None:
        for extension_id, properties in self._extensions_config.items():
            if key.startswith(f"{extension_id}."):
                name = key[len(extension_id) + 1 :]
                if name in properties:
                    return properties[name]
        return None

    def _setting_value_ok(self, key: str, value: Any) -> bool:
        if key == "obox.theme":
            return value in ("light", "dark")
        if key == "obox.language":
            return bool(self._language_code(str(value)))
        if key == "obox.close_action":
            return value in CLOSE_ACTIONS
        spec = self._setting_spec(key)
        if spec is None:
            return False
        kind = spec.get("type")
        if kind == "bool":
            return isinstance(value, bool)
        if kind == "enum":
            return value in (spec.get("enum") or [])
        return isinstance(value, str)

    def _on_settings_set(self, message: Any) -> None:
        payload = message.payload or {}
        key = str(payload.get("key") or "")
        value = payload.get("value")
        if not self._setting_value_ok(key, value):
            if message.correlation_id:
                self.bus.reply(message, {"ok": False, "error": f"非法设置：{key}"})
            return
        if key == "obox.theme":
            if not self.switch_theme(str(value)):
                if message.correlation_id:
                    self.bus.reply(message, {"ok": False, "error": "切换主题失败"})
                return
            self._settings[key] = value
            self._save_settings()
        elif key == "obox.close_action":
            self._set_close_action(str(value))
        elif key == "obox.language":
            if not self.switch_language(self._language_code(str(value))):
                if message.correlation_id:
                    self.bus.reply(message, {"ok": False, "error": "切换语言失败"})
                return
            self._settings[key] = value
            self._save_settings()
        else:
            self._settings[key] = value
            self._save_settings()
        self._push_settings()
        self._push_extension_configs()
        if message.correlation_id:
            self.bus.reply(message, {"ok": True})

    def _on_view_data(self, message: Any) -> None:
        payload = message.payload or {}
        view_id = str(payload.get("view_id") or "")
        spec = self._view_specs.get(view_id)
        entry = self._view_handles.get(view_id)
        if entry is None:
            if view_id.startswith("app."):
                app_entry = self._app_handles.get(view_id[len("app."):])
                if app_entry is not None and app_entry[0] == message.src:
                    try:
                        app_entry[1].set_data(dict(payload.get("data") or {}))
                    except Exception as exc:
                        print(f"[obox] 应用窗口数据注入失败：{exc}", file=sys.stderr)
            return
        if spec is None or str(spec.get("extension_id")) != message.src:
            return
        try:
            entry[1].set_data(dict(payload.get("data") or {}))
        except Exception as exc:
            print(f"[obox] 视图数据注入失败：{exc}", file=sys.stderr)

    def _view_payload(self, app: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": app["id"],
            "title": app.get("title", ""),
            "icon": app.get("icon", ""),
            "meta": app.get("meta", ""),
            "description": app.get("description", ""),
        }

    def _apps_payload(self) -> list[dict[str, Any]]:
        return [self._view_payload(app) for app in self._apps]

    def _apps_full_payload(self) -> list[dict[str, Any]]:
        return [
            {
                **self._view_payload(app),
                "author": app.get("publisher", ""),
                "version": app.get("version", ""),
            }
            for app in self._apps
        ]

    def _push_apps_list(self) -> None:
        self.bus.send(
            Message(
                src=OB_BOX,
                dst="app.obox",
                msg_id=APP_LIST_MSG,
                payload={"apps": self._apps_full_payload()},
            )
        )

    def _on_app_view_data(self, message: Any) -> None:
        """App 扩展过滤后把结果发回来，只接受本视图 owner 的消息与已知应用。"""
        payload = message.payload or {}
        view_id = str(payload.get("view_id") or "")
        spec = self._view_specs.get(view_id)
        if spec is None or str(spec.get("extension_id")) != message.src:
            return
        entry = self._view_handles.get(view_id)
        if entry is None:
            return
        allowed = {app["id"]: app for app in self._apps}
        filtered = [
            allowed[app["id"]]
            for app in payload.get("apps") or []
            if isinstance(app, dict) and app.get("id") in allowed
        ]
        try:
            entry[1].set_data({"apps": [self._view_payload(app) for app in filtered]})
        except Exception as exc:
            print(f"[obox] 应用过滤结果注入失败：{exc}", file=sys.stderr)

    def _sync_apps_data(self) -> None:
        for owner, handle in self._view_handles.values():
            if owner == "app.obox":
                handle.set_data({"apps": self._apps_payload()})

    def _on_component_event(self, message: Any) -> None:
        """obox 自己装配的视图（应用页）产生的点击。"""
        if message.src != OB_BOX:
            return
        value = (message.payload or {}).get("value")
        if value and str(message.id).startswith("app-card-"):
            self._open_app(str(value))

    # ---- 扩展管理 ----
    def disabled_extensions(self) -> list[str]:
        value = (self._load_config().get("extensions") or {}).get("disabled") or []
        return [str(item) for item in value]

    def _save_disabled_extensions(self, ids: list[str]) -> None:
        data = self._load_config()
        section = dict(data.get("extensions") or {})
        section["disabled"] = sorted({str(item) for item in ids})
        data["extensions"] = section
        self._save_config(data)
        self._sync_disabled_file()

    def _sync_disabled_file(self) -> None:
        """宿主启动时读这份镜像；来源仍是 config。"""
        install_dir = self.data_dir / "extensions"
        install_dir.mkdir(parents=True, exist_ok=True)
        (install_dir / "disabled.json").write_text(
            json.dumps(sorted(self.disabled_extensions()), ensure_ascii=False), encoding="utf-8"
        )

    def _push_extensions_list(self) -> None:
        if "extensions.main" not in self.window.view_ids():
            return
        disabled = set(self.disabled_extensions())
        items = []
        for item in self._extensions.values():
            entry = dict(item)
            entry["enabled"] = str(item.get("id")) not in disabled
            items.append(entry)
        items.sort(key=lambda entry: (str(entry.get("name") or ""), str(entry.get("id") or "")))
        self.bus.send(extensions_list_message(items))

    def install_extension(self, package: str) -> bool:
        """把选中的 .oix 复制到 incoming 再交给宿主安装。"""
        if not package:
            return False
        source = Path(package)
        if not source.is_file():
            self.window.notify_warning("安装扩展失败", f"文件不存在：{package}")
            return False
        incoming = self.data_dir / "extensions" / "incoming"
        incoming.mkdir(parents=True, exist_ok=True)
        for stale in incoming.glob("*.oix"):
            stale.unlink()
        target = incoming / source.name
        try:
            shutil.copyfile(source, target)
        except OSError as exc:
            self.window.notify_warning("安装扩展失败", str(exc))
            return False
        self.bus.send(install_extension_message(target.name))
        return True

    def remove_extension(self, extension_id: str, confirm: bool = True) -> bool:
        if not extension_id:
            return False
        if confirm:
            dialog = ConfirmDialog(
                "卸载扩展",
                f"将删除 {extension_id} 的安装目录与存储数据，确定继续吗？",
                self.window,
                confirm_text="卸载",
            )
            if not dialog.exec():
                return False
        self.bus.send(remove_extension_message(extension_id))
        return True

    def set_extension_enabled(self, extension_id: str, enabled: bool) -> bool:
        if not extension_id:
            return False
        ids = set(self.disabled_extensions())
        if enabled:
            ids.discard(extension_id)
        else:
            ids.add(extension_id)
        self._save_disabled_extensions(list(ids))
        self.bus.send(enable_extension_message(extension_id, enabled))
        return True

    def _on_extensions_manage(self, message: Any) -> None:
        payload = message.payload or {}
        action = str(payload.get("action") or "")
        extension_id = str(payload.get("id") or "")
        if action == "install":
            from PySide6.QtWidgets import QFileDialog

            package, _ = QFileDialog.getOpenFileName(
                self.window, "安装扩展", "", "obox 扩展 (*.oix)"
            )
            if package:
                self._show_progress(f"正在安装 {Path(package).name}，请稍候…")
                if not self.install_extension(package):
                    self._close_progress()
        elif action == "remove":
            self.remove_extension(extension_id)
        elif action == "toggle":
            self.set_extension_enabled(extension_id, bool(payload.get("enabled")))

    def _on_extensions_changed(self, message: Any) -> None:
        payload = message.payload or {}
        for extension_id, entries in (payload.get("i18n") or {}).items():
            for entry_id, values in entries.items():
                try:
                    self.i18n.register(str(extension_id), str(entry_id), values)
                except I18nError as exc:
                    print(f"[obox] {extension_id}.{entry_id} 注册失败：{exc}", file=sys.stderr)
        removed = [str(item) for item in payload.get("removed") or []]
        described = payload.get("extensions") or []
        for item in described:
            self._extensions[str(item["id"])] = dict(item)
        for extension_id in removed:
            self._extensions.pop(extension_id, None)
            self._extensions_config.pop(extension_id, None)
            self._extension_dirs.pop(extension_id, None)
            self.registry.unregister_owner(extension_id)
            ids = set(self.disabled_extensions())
            ids.discard(extension_id)
            self._save_disabled_extensions(list(ids))
        views = [dict(view) for view in payload.get("views") or []]
        kept = {str(view["view_id"]) for view in views}
        for view_id in list(self.window.view_ids()):
            if view_id in kept:
                continue
            if self.window.current_view_id() == view_id:
                fallback = "extensions.main" if "extensions.main" in self.window.view_ids() else DEFAULT_VIEW
                if fallback in self.window.view_ids():
                    self.window.show_view(fallback)
            self.window.remove_view(view_id)
            self._view_specs.pop(view_id, None)
            self._view_handles.pop(view_id, None)
        prepared: list[tuple[dict[str, Any], QWidget, list[str]]] = []
        for spec in views:
            view_id = str(spec["view_id"])
            self._view_specs[view_id] = spec
            directory = spec.get("directory")
            if directory:
                self._extension_dirs.setdefault(str(spec["extension_id"]), Path(str(directory)))
            if view_id in self.window.view_ids():
                continue
            mounted = self._mount_view(spec)
            if mounted is not None:
                prepared.append(mounted)
        if prepared:
            self._apply_extension_styles(prepared)
        self._extensions_config = {
            extension_id: dict(item.get("configuration") or {})
            for extension_id, item in self._extensions.items()
            if item.get("status") == "active"
        }
        self._rebuild_apps()
        self._push_apps_list()
        self._push_settings()
        self._push_extensions_list()
        if self._tray is not None:
            self._refresh_tray()

    def _show_progress(self, message: str) -> None:
        self._close_progress()
        dialog = InstallProgressDialog("安装扩展", message, self.window)
        dialog.show()
        self._progress_dialog = dialog
        QTimer.singleShot(30000, self._progress_timeout)

    def _progress_timeout(self) -> None:
        if self._progress_dialog is None:
            return
        self._close_progress()
        self.window.notify_warning("安装扩展超时", "宿主没有在 30 秒内返回结果，请查看日志或重试")

    def _close_progress(self) -> None:
        dialog = self._progress_dialog
        self._progress_dialog = None
        if dialog is not None:
            dialog.hide()
            dialog.deleteLater()

    def _on_extension_result(self, message: Any) -> None:
        payload = message.payload or {}
        action = str(payload.get("action") or "")
        extension_id = str(payload.get("id") or "")
        if action == "install":
            self._close_progress()
        if payload.get("ok"):
            labels = {
                "install": "扩展已安装并激活",
                "remove": "扩展已卸载",
                "toggle": "扩展状态已更新",
            }
            self.window.notify_warning(labels.get(action, "扩展操作完成"), extension_id or "")
            return
        labels = {
            "install": "安装扩展失败",
            "remove": "卸载扩展失败",
            "toggle": "扩展状态更新失败",
        }
        self.window.notify_warning(labels.get(action, "扩展操作失败"), str(payload.get("error") or "未知原因"))

    def _on_app_launch(self, message: Any) -> None:
        payload = message.payload or {}
        if payload.get("app_id"):
            self._open_app(str(payload["app_id"]))

    def _open_app(self, app_id: str) -> None:
        app = next((item for item in self._apps if item["id"] == app_id), None)
        if app is None:
            print(f"[obox] 未知应用：{app_id}", file=sys.stderr)
            return
        single = bool(app.get("single", True))
        persistent = bool(app.get("persistent", False)) and single
        if single:
            existing = self._app_windows.get(app_id)
            if existing is not None:
                if existing.is_closed_by_user() and not persistent:
                    existing.force_close()
                    self._app_windows.pop(app_id, None)
        window = AppWindow(str(app.get("title") or app_id), persistent=persistent)
        application = QApplication.instance()
        if application is not None and not application.windowIcon().isNull():
            window.setWindowIcon(application.windowIcon())
        if self.provider is not None:
            window.setStyleSheet(self.provider.stylesheet)
        window.destroyed.connect(lambda *_: self._app_handles.pop(window_id, None))
        window.destroyed.connect(lambda *_: self._app_windows.pop(window_id, None))
        self._app_windows[window_id] = window
        self._app_specs[window_id] = app
        window.show()
        window.raise_()
        self.bus.send(app_open_message(app_id, window_id, str(app["extension_id"])))
        QTimer.singleShot(3000, lambda: self._app_timeout(window_id))

    def _app_timeout(self, window_id: str) -> None:
        window = self._app_windows.get(window_id)
        if window is not None and not window.has_content():
            window.show_message(self.i18n.translate("{{i18n.apps.timeout}}", "obox"))

    def _on_app_ui(self, message: Any) -> None:
        payload = message.payload or {}
        window_id = str(payload.get("window_id") or "")
        window = self._app_windows.get(window_id)
        if window is None:
            return
        owner = message.src
        source = str(payload.get("oml") or "")
        if source:
            directory = self._extension_dirs.get(owner) or Path("")
            try:
                source = load_oml(directory, source)
            except OmlError as exc:
                window.show_message(str(exc))
                return
        else:
            source = str(payload.get("html") or "")
        if not source:
            window.show_message(self.i18n.translate("{{i18n.apps.noui}}", "obox"))
            return
        source = self.i18n.translate(source, owner)
        handle_out: dict[str, Any] = {}
        try:
            root, _ids = self.assemble_view(owner, source, handle_out=handle_out)
        except OboxError as exc:
            window.show_message(str(exc))
            return
        window.set_content(root)
        handle = handle_out.get("handle")
        if handle is not None:
            self._app_handles[window_id] = (owner, handle)

    def _owned_component(self, owner: str, component_id: str):
        try:
            return self.registry.lookup(owner, component_id)
        except ComponentNotFound:
            actual_owner = self.registry.owner_of(component_id)
            if actual_owner is not None and actual_owner != owner:
                raise ForbiddenOwner(f"组件 {component_id} 属于 {actual_owner}，不允许 {owner} 修改")
            raise

    def _reply_error(self, message: Any, exc: BaseException) -> None:
        if message.correlation_id:
            self.bus.reply(message, error_payload(exc))

    def attach_instance(self, instance: SingleInstance) -> None:
        self._single = instance
        instance.show_requested.connect(self._restore_window)

    def _setup_tray(self) -> None:
        if not TrayIcon.available():
            return
        self._tray = TrayIcon(self.window.windowIcon(), self.window)
        self._tray.show_requested.connect(self._restore_window)
        self._tray.settings_requested.connect(self._open_settings)
        self._tray.quit_requested.connect(self._quit)
        self._tray.reload_requested.connect(self.reload_extensions)
        self._tray.open_extensions_requested.connect(self._open_extensions_dir)
        self._tray.theme_requested.connect(self._switch_theme_from_tray)
        self._tray.language_requested.connect(self._switch_language_from_tray)
        self._refresh_tray()
        self._apply_tray_styles()
        self._tray.show()

    def _refresh_tray(self) -> None:
        tray = self._tray
        if tray is None:
            return
        labels_by_mode = {"light": "浅色", "dark": "深色"}
        themes = [
            (kit.name, labels_by_mode.get(kit.mode, kit.name))
            for kit in scan_themes([self.themes_root, self.user_themes_root])
        ]
        tray.set_theme_options(themes, self.theme_name)
        tray.set_language_options(self.language_options(), self.i18n.language)

    def _apply_tray_styles(self) -> None:
        if self._tray is not None and self.provider is not None:
            self._tray.apply_stylesheet(str(getattr(self.provider, "stylesheet", "")))

    def _switch_theme_from_tray(self, name: str) -> None:
        if self.switch_theme(name):
            self._settings["obox.theme"] = name
            self._save_settings()
            self._refresh_tray()

    def _switch_language_from_tray(self, code: str) -> None:
        if self.switch_language(code):
            self._settings["obox.language"] = code
            self._save_settings()
            self._refresh_tray()

    def _open_extensions_dir(self) -> None:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.extensions_root)))

    def reload_extensions(self) -> None:
        if self._reloading:
            return
        self._reloading = True
        if self._tray is not None:
            self._tray.set_enabled(False)
        self._restore_target = self.window.current_view_id()
        for owner in {spec["extension_id"] for spec in self._view_specs.values()}:
            self.registry.unregister_owner(owner)
        self.window.clear_views()
        self._view_specs.clear()
        self._view_handles.clear()
        self.supervisor.restart()

    def _finish_reload(self) -> None:
        if not self._reloading:
            return
        self._reloading = False
        target = self._restore_target
        self._restore_target = ""
        if target:
            self._restore_view(target)
        if self._tray is not None:
            self._tray.set_enabled(True)
        self.window.notify_warning("扩展已刷新", "宿主已重启，视图已恢复")

    def _restore_window(self) -> None:
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _open_settings(self) -> None:
        self._restore_window()
        self.window.show_view("settings.main")

    def _on_close_requested(self) -> None:
        if self.close_action == "ask":
            dialog = CloseDialog(self.window)
            accepted = bool(dialog.exec())
            final, persisted = decide_close("ask", dialog.choice, dialog.remember)
            if persisted:
                self._set_close_action(persisted)
            if not accepted or final == "cancel":
                return
        else:
            final, _ = decide_close(self.close_action)
        if final == "quit":
            self._quit()
        else:
            self._to_tray()

    def _set_close_action(self, action: str) -> None:
        if action not in CLOSE_ACTIONS:
            return
        self.close_action = action
        self._settings["obox.close_action"] = action
        self._save_settings()
        self._push_settings()

    def _to_tray(self) -> None:
        if self._tray is None:
            self._quit()
            return
        self.window.hide()
        self._tray.show()

    def _quit(self) -> None:
        if self._tray is not None:
            self._tray.hide()
        self.window.allow_close()
        self.window.close()
        self.shutdown()
        instance = QApplication.instance()
        if instance is not None:
            instance.quit()

    def shutdown(self) -> None:
        if getattr(self, "_stopped", False):
            return
        self._stopped = True
        if self._tray is not None:
            self._tray.hide()
            self._tray.deleteLater()
            self._tray = None
        if self._watch_timer is not None:
            self._watch_timer.stop()
            self._watch_timer = None
        try:
            self.supervisor.stop()
        except Exception as exc:
            print(f"[obox] 停止宿主失败：{exc}", file=sys.stderr)
        self.window.allow_close()


def run(
    extensions_dir: str = "",
    exit_after: float = 0.0,
    theme: str = "",
    language: str = "",
) -> int:
    apply_app_user_model_id()
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication.instance() or QApplication(sys.argv[:1])
    icon_path = Path(__file__).resolve().parent / "assets" / "obox.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    instance = SingleInstance()
    if instance.try_notify():
        return 0
    instance.listen()
    paths = resolve_paths()
    project_root = paths.program_dir
    try:
        obox_app = OboxApp(project_root, extensions_dir, theme, language, data_dir=paths.data_dir)
        obox_app.attach_instance(instance)
        obox_app.start()
    except OboxError as exc:
        print(f"[obox] 启动失败：{exc}", file=sys.stderr)
        return 2
    if exit_after > 0:
        QTimer.singleShot(int(exit_after * 1000), app.quit)
    try:
        return app.exec()
    finally:
        obox_app.shutdown()
        instance.close()
