"""开机自启动：注册表写入、删除与源码运行不可用。"""

from __future__ import annotations

import sys
import types

from obox.core import autostart


class _FakeKey:
    def __init__(self, store, name):
        self.store = store
        self.name = name

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeWinreg(types.ModuleType):
    HKEY_CURRENT_USER = object()
    REG_SZ = 1

    def __init__(self):
        super().__init__("winreg")
        self.values: dict[str, str] = {}

    def OpenKey(self, root, path):
        return _FakeKey(self.values, path)

    def CreateKey(self, root, path):
        return _FakeKey(self.values, path)

    def QueryValueEx(self, key, name):
        if name not in self.values:
            raise FileNotFoundError(name)
        return self.values[name], 1

    def SetValueEx(self, key, name, reserved, kind, value):
        self.values[name] = value

    def DeleteValue(self, key, name):
        if name not in self.values:
            raise FileNotFoundError(name)
        del self.values[name]


def _install(monkeypatch, fake):
    monkeypatch.setattr(autostart.sys, "platform", "win32")
    monkeypatch.setattr(autostart, "_packaged", lambda: True)
    monkeypatch.setitem(sys.modules, "winreg", fake)


def test_enable_writes_executable_path(monkeypatch):
    fake = _FakeWinreg()
    _install(monkeypatch, fake)
    assert autostart.set_enabled(True) is True
    assert fake.values["obox"] == autostart.command()
    assert autostart.command().endswith('.exe"') or autostart.command().endswith('python.exe"')


def test_enable_then_disable(monkeypatch):
    fake = _FakeWinreg()
    _install(monkeypatch, fake)
    autostart.set_enabled(True)
    assert autostart.is_enabled() is True
    assert autostart.set_enabled(False) is True
    assert autostart.is_enabled() is False


def test_disabled_when_not_packaged(monkeypatch):
    fake = _FakeWinreg()
    monkeypatch.setattr(autostart.sys, "platform", "win32")
    monkeypatch.setattr(autostart, "_packaged", lambda: False)
    monkeypatch.setitem(sys.modules, "winreg", fake)
    assert autostart.is_supported() is False
    assert autostart.set_enabled(True) is False
    assert fake.values == {}


def test_write_failure_returns_false(monkeypatch):
    class Broken(_FakeWinreg):
        def CreateKey(self, root, path):
            raise OSError("denied")

    _install(monkeypatch, Broken())
    assert autostart.set_enabled(True) is False
