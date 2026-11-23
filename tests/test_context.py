from __future__ import annotations

from pathlib import Path

import pytest

from obox.api.errors import OboxError
from obox.core.bus import MessageBus
from obox.extensions.contributions import CommandRegistry, ViewRegistry
from obox.extensions.context import ExtensionContext
from obox.extensions.manifest import Manifest

MANIFEST = Manifest(
    name="demo",
    version="0.1.0",
    publisher="obox",
    description="d",
    main="extension.py",
    icon="main.svg",
    activation_events=("onStartup",),
    contributes={},
    directory=Path(__file__).resolve().parent.parent / "extensions" / "demo",
)


def _context() -> tuple[ExtensionContext, CommandRegistry, ViewRegistry]:
    commands, views = CommandRegistry(), ViewRegistry()
    bus = MessageBus("demo.obox")
    context = ExtensionContext(MANIFEST, Path("."), bus, commands, views)
    return context, commands, views


def test_command_registration(tmp_path: Path) -> None:
    context, commands, _ = _context()
    context.register_command("demo.hello", lambda: "hi")
    assert commands.invoke("demo.hello") == "hi"


def test_duplicate_command_rejected(tmp_path: Path) -> None:
    context, _, _ = _context()
    context.register_command("demo.hello", lambda: None)
    with pytest.raises(OboxError):
        context.register_command("demo.hello", lambda: None)


def test_view_registration() -> None:
    context, _, views = _context()
    context.register_view("demo.main", "<Div id=\"a\"></Div>", "sidebar", "示范")
    assert views.get("demo.main").title == "示范"


def test_dispose_clears_subscriptions() -> None:
    context, commands, views = _context()
    context.register_command("demo.hello", lambda: None)
    context.register_view("demo.main", "<Div id=\"a\"></Div>")
    context.dispose()
    assert commands.ids() == []
    assert views.ids() == []


def test_read_asset_rejects_escape() -> None:
    context, _, _ = _context()
    with pytest.raises(ValueError):
        context.read_asset("../../pyproject.toml")