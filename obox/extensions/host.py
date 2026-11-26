"""扩展宿主进程入口：python -m obox.extensions.host --pipe ... --token ...。"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import logging
import shutil
import sys
import threading
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any

from obox.qt import QCoreApplication, QObject, QTimer

from ..core.bus import MessageBus
from ..core.ipc.client import IpcClient
from .context import ExtensionContext
from .contributions import CommandRegistry, ViewRegistry
from ..api.errors import ManifestError
from ..api.message import OB_BOX
from ..i18n import I18nError, parse_document
from ..api.extensions import (
    EXT_ENABLE_MSG,
    EXT_INSTALL_MSG,
    EXT_REMOVE_MSG,
    HOST_ID,
    extensions_changed_message,
    extensions_result_message,
)
from .loader import (
    arch_matches,
    current_arch,
    install_one,
    install_packages,
    package_arch,
    remove_one,
    scan_all,
)
from .manifest import Manifest, load_manifest

LOGGER = logging.getLogger(__name__)


class AsyncRuntime:
    """宿主里的 asyncio 线程；扩展协程跑在这里，Qt 主循环只负责管道 I/O。"""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, name="obox-asyncio", daemon=True)

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def start(self) -> None:
        self._thread.start()

    def submit(self, coro: Any) -> None:
        asyncio.run_coroutine_threadsafe(coro, self._loop)

    def stop(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)


class ExtensionHost(QObject):
    """负责激活扩展、分发事件并把注册点回传给 obox。"""

    def __init__(
        self,
        extensions_dir: Path,
        install_dir: Path,
        client: IpcClient,
        storage_root: Path,
        system_dir: Path | None = None,
        dev_dirs: list[Path] | None = None,
    ) -> None:
        super().__init__()
        self._extensions_dir = extensions_dir
        self._dev_dirs = list(dev_dirs or [])
        self._system_dir = system_dir or extensions_dir
        self._install_dir = install_dir
        self._client = client
        self._storage_root = storage_root
        self._bus = MessageBus(local_id=HOST_ID)
        self._bus.attach_transport(client)
        self._commands = CommandRegistry()
        self._views = ViewRegistry()
        self._runtime = AsyncRuntime()
        self._modules: dict[str, ModuleType] = {}
        self._contexts: dict[str, ExtensionContext] = {}
        self._manifests: dict[str, Manifest] = {}
        self._i18n: dict[str, dict[str, dict[str, str]]] = {}
        self._disabled: set[str] = set()
        self._origins: dict[str, str] = {}
        self._disabled_path = self._install_dir / "disabled.json"
        self._incoming = self._install_dir / "incoming"
        self._bus.on(EXT_INSTALL_MSG, self._on_install)
        self._bus.on(EXT_REMOVE_MSG, self._on_remove)
        self._bus.on(EXT_ENABLE_MSG, self._on_enable)

    def _read_disabled(self) -> set[str]:
        try:
            data = json.loads(self._disabled_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return set()
        if isinstance(data, list):
            return {str(item) for item in data}
        return set()

    def _write_disabled(self) -> None:
        try:
            self._install_dir.mkdir(parents=True, exist_ok=True)
            self._disabled_path.write_text(
                json.dumps(sorted(self._disabled), ensure_ascii=False), encoding="utf-8"
            )
        except OSError as exc:
            LOGGER.warning("禁用名单写入失败：%s", exc)

    def _from_obox(self, message: Any) -> bool:
        return str(getattr(message, "src", "")) == OB_BOX

    def _on_install(self, message: Any) -> None:
        if not self._from_obox(message):
            return
        name = Path(str((message.payload or {}).get("package") or "")).name
        if not name.endswith(".oix"):
            self._reply_install("", False, "安装包必须是以 .oix 结尾的文件")
            return
        if not arch_matches(name):
            wanted = package_arch(name)
            self._reply_install("", False, f"安装包架构是 {wanted}，当前进程是 {current_arch()}，请选择对应架构的包")
            return
        package = self._incoming / name
        try:
            target = install_one(package, self._install_dir)
        except (OSError, zipfile.BadZipFile, ManifestError) as exc:
            self._reply_install("", False, str(exc))
            return
        finally:
            try:
                package.unlink()
            except OSError:
                pass
        try:
            manifest = load_manifest(target)
        except ManifestError as exc:
            self._reply_install("", False, str(exc))
            return
        extension_id = manifest.extension_id
        self._deactivate(extension_id)
        self._disabled.discard(extension_id)
        results = self._activate(manifest, target, "user")
        ok = bool(results) and all(item.get("status") == "active" for item in results)
        error = "" if ok else str(results[0].get("error", "")) if results else "激活失败"
        self._reply_install(extension_id, ok, error)
        self._push_changed(changed=[extension_id])

    def _reply_install(self, extension_id: str, ok: bool, error: str) -> None:
        self._bus.send(extensions_result_message("install", extension_id, ok, error))

    def _on_remove(self, message: Any) -> None:
        if not self._from_obox(message):
            return
        extension_id = str((message.payload or {}).get("id") or "")
        if not extension_id or not (self._install_dir / extension_id).is_dir():
            self._bus.send(extensions_result_message("remove", extension_id, False, "只允许卸载用户安装的扩展"))
            return
        self._deactivate(extension_id)
        remove_one(self._install_dir, extension_id)
        storage = self._storage_root / extension_id
        if storage.is_dir():
            shutil.rmtree(storage, ignore_errors=True)
        self._disabled.discard(extension_id)
        self._bus.send(extensions_result_message("remove", extension_id, True))
        self._push_changed(removed=[extension_id])

    def _on_enable(self, message: Any) -> None:
        if not self._from_obox(message):
            return
        payload = message.payload or {}
        extension_id = str(payload.get("id") or "")
        enabled = bool(payload.get("enabled"))
        directory = self._install_dir / extension_id
        if not extension_id or not (directory / "extension.json").is_file():
            self._bus.send(
                extensions_result_message(
                    "toggle", extension_id, False, "系统与源码扩展不可停用"
                )
            )
            return
        if enabled:
            self._disabled.discard(extension_id)
            manifest = load_manifest(directory)
            self._deactivate(extension_id)
            self._activate(manifest, directory, "user")
        else:
            self._disabled.add(extension_id)
            self._deactivate(extension_id)
        self._bus.send(extensions_result_message("toggle", extension_id, True))
        self._push_changed(changed=[extension_id])

    def _deactivate(self, extension_id: str) -> None:
        module = self._modules.pop(extension_id, None)
        context = self._contexts.pop(extension_id, None)
        if module is not None and context is not None:
            try:
                result = module.deactivate(context)
                if asyncio.iscoroutine(result):
                    self._runtime.submit(result)
            except Exception as exc:  # 单个扩展停用失败不影响其它
                LOGGER.warning("停用 %s 失败：%s", extension_id, exc)
        if context is not None:
            context.dispose()
        self._views.unregister_owner(extension_id)
        self._commands.unregister_owner(extension_id)
        self._manifests.pop(extension_id, None)
        self._i18n.pop(extension_id, None)
        self._bus.local_ids.discard(extension_id)

    def _views_payload(self) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for view in self._views.all():
            manifest = self._manifests.get(view.extension_id)
            if manifest is None:
                continue
            payload.append(
                {
                    "view_id": view.view_id,
                    "extension_id": view.extension_id,
                    "container": view.container,
                    "html": view.html_source,
                    "title": view.title,
                    "icon_path": str(manifest.icon_path),
                    "directory": str(manifest.directory),
                }
            )
        return payload

    def _statuses(self) -> list[dict[str, Any]]:
        """当前激活与禁用扩展的快照，供 obox 直接覆盖状态。"""
        items: list[dict[str, Any]] = []
        for extension_id, manifest in self._manifests.items():
            status = "disabled" if extension_id in self._disabled else "active"
            items.append({**self._describe(manifest), "status": status})
        return items

    def _push_changed(self, removed: list[str] | None = None, changed: list[str] | None = None) -> None:
        described = [self._describe(self._manifests[key]) for key in (changed or []) if key in self._manifests]
        self._bus.send(
            extensions_changed_message(
                removed or [],
                changed or [],
                self._views_payload(),
                self._commands.ids(),
                described,
            )
        )

    def start(self) -> None:
        self._runtime.start()
        self.activate_all()

    def activate_all(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        self._disabled = self._read_disabled()
        try:
            for path in install_packages(self._install_dir):
                LOGGER.info("已安装扩展包：%s", path)
        except OSError as exc:
            LOGGER.warning("安装扩展包失败：%s", exc)
        roots = [(self._install_dir, "user")]
        if self._system_dir.resolve() != self._extensions_dir.resolve():
            roots.append((self._system_dir, "system"))
        roots.append((self._extensions_dir, "source"))
        for info in scan_all(roots):
            if info.manifest is None:
                results.append({"id": info.directory.name, "status": "invalid", "error": info.error})
                continue
            if info.manifest.extension_id in self._disabled:
                self._manifests[info.manifest.extension_id] = info.manifest
                self._origins[info.manifest.extension_id] = info.origin
                results.append(
                    {**self._describe(info.manifest), "status": "disabled", "origin": info.origin}
                )
                continue
            results.extend(self._activate(info.manifest, info.directory, info.origin))
        for directory in self._dev_dirs:
            try:
                manifest = load_manifest(directory)
            except Exception as exc:
                results.append({"id": directory.name, "status": "invalid", "error": str(exc)})
                continue
            extension_id = manifest.extension_id
            if extension_id in self._modules:
                self._deactivate(extension_id)
            results.extend(self._activate(manifest, directory, "dev"))
        self._client.send(
            {
                "type": "status",
                "extensions": results,
                "i18n": self._i18n,
                "views": [
                    {
                        "view_id": view.view_id,
                        "extension_id": view.extension_id,
                        "container": view.container,
                        "html": view.html_source,
                        "title": view.title,
                        "icon_path": str(self._manifests[view.extension_id].icon_path),
                        "directory": str(self._manifests[view.extension_id].directory),
                    }
                    for view in self._views.all()
                ],
                "commands": self._commands.ids(),
            }
        )
        return results

    def _load_i18n(self, directory: Path) -> dict[str, dict[str, str]]:
        path = directory / "i18n.json"
        if not path.is_file():
            return {}
        try:
            return parse_document(json.loads(path.read_text(encoding="utf-8")), str(path))
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.warning("读取 %s 失败：%s", path, exc)
        except I18nError as exc:
            LOGGER.warning("%s 不合法：%s", path, exc)
        return {}

    def _activate(self, manifest: Manifest, directory: Path, origin: str = "source") -> list[dict[str, Any]]:
        try:
            module = self._load_module(manifest)
            self._i18n[manifest.extension_id] = self._load_i18n(directory)
            storage = self._storage_root / manifest.extension_id
            storage.mkdir(parents=True, exist_ok=True)
            context = ExtensionContext(manifest, storage, self._bus, self._commands, self._views)
            self._bus.add_local(manifest.extension_id)
            result = module.activate(context)
            if asyncio.iscoroutine(result):
                self._runtime.submit(result)
            self._modules[manifest.extension_id] = module
            self._contexts[manifest.extension_id] = context
            self._manifests[manifest.extension_id] = manifest
            self._origins[manifest.extension_id] = origin
            missing = self._missing_contributions(manifest)
            if missing:
                return [{**self._describe(manifest), "status": "failed", "error": missing, "origin": origin}]
            return [{**self._describe(manifest), "status": "active", "origin": origin}]
        except Exception as exc:  # 单个扩展失败不影响其他扩展
            self._views.unregister_owner(manifest.extension_id)
            self._commands.unregister_owner(manifest.extension_id)
            self._manifests.pop(manifest.extension_id, None)
            self._i18n.pop(manifest.extension_id, None)
            self._bus.local_ids.discard(manifest.extension_id)
            return [{**self._describe(manifest), "status": "failed", "error": str(exc), "origin": origin}]

    def _describe(self, manifest: Manifest) -> dict[str, Any]:
        return {
            "id": manifest.extension_id,
            "name": manifest.name,
            "publisher": manifest.publisher,
            "version": manifest.version,
            "description": manifest.description,
            "icon_path": str(manifest.icon_path),
            "directory": str(manifest.directory),
            "app_id": manifest.app_id,
            "app_title": manifest.app_title,
            "apps": manifest.apps,
            "configuration": manifest.configuration,
            "origin": self._origins.get(manifest.extension_id, "source"),
        }

    def _missing_contributions(self, manifest: Manifest) -> str:
        """清单声明了但 activate 里没有注册的注册点。"""
        declared_views = [str(item.get("id")) for item in manifest.contributes.get("views", [])]
        declared_commands = [str(item.get("command")) for item in manifest.contributes.get("commands", [])]
        missing_views = [view_id for view_id in declared_views if view_id not in self._views.ids()]
        missing_commands = [cmd for cmd in declared_commands if cmd not in self._commands.ids()]
        problems = []
        if missing_views:
            problems.append(f"未注册视图：{', '.join(missing_views)}")
        if missing_commands:
            problems.append(f"未注册命令：{', '.join(missing_commands)}")
        return "；".join(problems)

    def _load_module(self, manifest: Manifest) -> ModuleType:
        """优先加载编译后的 extension.pyd，否则回退源码；两种都注入模块搜索路径。"""
        directory = str(manifest.directory)
        if directory not in sys.path:
            sys.path.insert(0, directory)
        pyd = manifest.directory / "extension.pyd"
        target = pyd if pyd.exists() else manifest.directory / manifest.main
        module_name = "extension" if pyd.exists() else f"obox_ext_{manifest.name}_{manifest.publisher}"
        if module_name in sys.modules and pyd.exists():
            LOGGER.warning("模块名 extension 已被占用，覆盖加载 %s", manifest.extension_id)
        spec = importlib.util.spec_from_file_location(module_name, target)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载扩展入口：{target}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        if not hasattr(module, "activate") or not hasattr(module, "deactivate"):
            raise ImportError("扩展必须定义 activate 与 deactivate")
        return module

    def receive_frame(self, frame: dict[str, Any]) -> None:
        """控制帧交给宿主自己，消息帧交给总线。"""
        if "type" in frame:
            self.handle_control(frame)
            return
        self._bus.receive(frame)

    def handle_control(self, frame: dict[str, Any]) -> None:
        kind = frame.get("type")
        if kind == "command":
            command_id = str(frame.get("command", ""))
            try:
                self._commands.invoke(command_id)
                self._client.send({"type": "command_result", "command": command_id, "ok": True})
            except Exception as exc:
                self._client.send(
                    {"type": "command_result", "command": command_id, "ok": False, "error": str(exc)}
                )
        elif kind == "shutdown":
            self.shutdown()

    def shutdown(self) -> None:
        for extension_id, context in list(self._contexts.items()):
            module = self._modules.get(extension_id)
            try:
                if module is not None:
                    result = module.deactivate(context)
                    if asyncio.iscoroutine(result):
                        self._runtime.submit(result)
            finally:
                context.dispose()
        self._contexts.clear()
        self._modules.clear()
        self._runtime.stop()
        QCoreApplication.quit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="obox 扩展宿主进程")
    parser.add_argument("--pipe", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--extensions-dir", required=True)
    parser.add_argument("--system-dir", default="")
    parser.add_argument("--install-dir", required=True)
    parser.add_argument("--storage-dir", required=True)
    parser.add_argument("--dev-dir", action="append", default=[], help="开发中的扩展目录，可重复")
    args = parser.parse_args(argv)

    app = QCoreApplication(sys.argv[:1])
    client = IpcClient()
    host = ExtensionHost(
        Path(args.extensions_dir),
        Path(args.install_dir),
        client,
        Path(args.storage_dir),
        Path(args.system_dir) if args.system_dir else None,
        [Path(item) for item in args.dev_dir],
    )
    client.frame_received.connect(host.receive_frame)
    client.connected.connect(host.start)

    def _retry(attempt: int = 0) -> None:
        try:
            client.connect_to(args.pipe, args.token)
        except Exception:
            if attempt >= 20:
                QCoreApplication.exit(1)
                return
            QTimer.singleShot(250, lambda: _retry(attempt + 1))

    _retry()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())