"""OboxContext 不可变约束。"""

from __future__ import annotations

from pathlib import Path

import pytest

from obox.extensions.context import OboxContext, SubscriptionBag
from obox.extensions.manifest import load_manifest


def _ctx(tmp_path: Path) -> OboxContext:
    dev = tmp_path / "ext"
    (dev / "assets").mkdir(parents=True)
    (dev / "views").mkdir()
    (dev / "assets" / "main.svg").write_text("<svg/>", encoding="utf-8")
    (dev / "extension.json").write_text(
        '{"name":"ctx","version":"1.0.0","publisher":"obox","description":"d","main":"extension.py","icon":"main.svg"}',
        encoding="utf-8",
    )
    (dev / "extension.py").write_text("def activate(context):\n    pass\n", encoding="utf-8")
    manifest = load_manifest(dev)
    return OboxContext(manifest, tmp_path / "storage", None, None, None)  # type: ignore[arg-type]


def test_context_fields_are_read_only(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    with pytest.raises(AttributeError):
        ctx.extension_id = "other"
    with pytest.raises(AttributeError):
        ctx.window_id = "w1"
    assert isinstance(ctx.subscriptions, SubscriptionBag)


def test_subscription_bag_supports_append_and_clear() -> None:
    bag = SubscriptionBag()
    seen: list[str] = []
    bag.append(lambda: seen.append("disposed"))
    assert len(bag) == 1
    bag.dispose()
    assert seen == ["disposed"]
    assert len(bag) == 0
    bag.append(lambda: None)
    bag.clear()
    assert len(bag) == 0


def test_absolute_path_rejects_escape(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    assert ctx.as_absolute_path("assets/main.svg").name == "main.svg"
    with pytest.raises(ValueError):
        ctx.as_absolute_path("../outside.txt")

def test_bound_namespaces_inject_ctx(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path)
    message = ctx.window.showInformationMessage("hello", "ok")
    assert message.msg_id.startswith("WINDOW_SHOW_INFORMATION")
    assert message.src == ctx.extension_id
    assert ctx.storage.globalState.get.__name__ == "<lambda>" or callable(ctx.storage.globalState.get)
