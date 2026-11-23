from __future__ import annotations

from pathlib import Path

from obox.api.component import ComponentModifyMessage, ComponentStateMessage
from obox.app import OboxApp
from tests.fake_provider import build_provider

ROOT = Path(__file__).resolve().parent.parent


class FakeTransport:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    def send(self, data: dict) -> None:
        self.sent.append(data)


class FakeComponent:
    state_accessors = {"value": ("get_value", "set_value")}

    def __init__(self, owner: str, component_id: str, value: str = "old") -> None:
        self.owner = owner
        self.id = component_id
        self.value = value

    def get_value(self) -> str:
        return self.value

    def set_value(self, value: str) -> None:
        self.value = value


def _app(qapp) -> tuple[OboxApp, FakeTransport]:
    app = OboxApp(ROOT, provider=build_provider())
    transport = FakeTransport()
    app.bus.attach_transport(transport)
    return app, transport


def test_modify_missing_component_replies_error(qapp) -> None:
    app, transport = _app(qapp)
    app.bus.receive(
        ComponentModifyMessage(
            src="demo.obox",
            dst="obox",
            component_id="nope",
            state_type="value",
            value=1,
            correlation_id="c1",
        ).to_dict()
    )
    frame = transport.sent[-1]
    assert frame["reply"] is True
    assert frame["payload"]["error"] == "E_COMPONENT_NOT_FOUND"


def test_modify_foreign_component_replies_forbidden(qapp) -> None:
    app, transport = _app(qapp)
    app.registry.register("other.x", "inp", FakeComponent("other.x", "inp"))
    app.bus.receive(
        ComponentModifyMessage(
            src="demo.obox",
            dst="obox",
            component_id="inp",
            state_type="value",
            value="hacked",
            correlation_id="c2",
        ).to_dict()
    )
    frame = transport.sent[-1]
    assert frame["payload"]["error"] == "E_FORBIDDEN_OWNER"
    assert app.registry.lookup("other.x", "inp").value == "old"


def test_modify_own_component_applies(qapp) -> None:
    app, transport = _app(qapp)
    app.registry.register("demo.obox", "inp", FakeComponent("demo.obox", "inp"))
    app.bus.receive(
        ComponentModifyMessage(
            src="demo.obox",
            dst="obox",
            component_id="inp",
            state_type="value",
            value="new",
            correlation_id="c3",
        ).to_dict()
    )
    assert transport.sent[-1]["payload"]["ok"] is True
    assert app.registry.lookup("demo.obox", "inp").value == "new"


def test_unsupported_state_rejected(qapp) -> None:
    app, transport = _app(qapp)
    app.registry.register("demo.obox", "inp", FakeComponent("demo.obox", "inp"))
    app.bus.receive(
        ComponentStateMessage(
            src="demo.obox",
            dst="obox",
            component_id="inp",
            state_type="checked",
            correlation_id="c4",
        ).to_dict()
    )
    assert transport.sent[-1]["payload"]["error"] == "E_KIT_CONTRACT"


def test_fire_and_forget_does_not_crash(qapp) -> None:
    app, transport = _app(qapp)
    app.registry.register("demo.obox", "inp", FakeComponent("demo.obox", "inp"))
    app.bus.receive(
        ComponentModifyMessage(
            src="demo.obox", dst="obox", component_id="inp", state_type="value", value="x"
        ).to_dict()
    )
    assert transport.sent == []
