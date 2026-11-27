"""开机自启动：读写当前用户的 Run 键，不依赖 Qt。"""

from __future__ import annotations

import os
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "obox"


def _winreg():
    if sys.platform != "win32":
        return None
    import winreg

    return winreg


def _packaged() -> bool:
    """与 extensions/supervisor.py 的判据保持一致：源码运行不写自启动。"""
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        return True
    return not sys.executable.lower().endswith(("python.exe", "pythonw.exe"))


def is_supported() -> bool:
    """仅打包运行且 Windows 上可用。"""
    return _winreg() is not None and _packaged()


def command() -> str:
    return f'"{os.path.abspath(sys.executable)}"'


def is_enabled() -> bool:
    registry = _winreg()
    if registry is None or not _packaged():
        return False
    try:
        with registry.OpenKey(registry.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _kind = registry.QueryValueEx(key, VALUE_NAME)
    except OSError:
        return False
    return bool(str(value).strip())


def set_enabled(enabled: bool) -> bool:
    """写或删 Run 键；失败返回 False，调用方负责回滚界面状态。"""
    registry = _winreg()
    if registry is None or not _packaged():
        return False
    try:
        with registry.CreateKey(registry.HKEY_CURRENT_USER, RUN_KEY) as key:
            if enabled:
                registry.SetValueEx(key, VALUE_NAME, 0, registry.REG_SZ, command())
            else:
                try:
                    registry.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
    except OSError:
        return False
    return True
