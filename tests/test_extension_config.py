"""扩展配置下发：激活后与变更后各一次，只含自己的键。"""

from __future__ import annotations

from pathlib import Path

from obox.app import OboxApp
from tests.fake_provider import build_provider

ROOT = Path(__file__).resolve().parent.parent


def _app(tmp_path: Path) -> OboxApp:
    return OboxApp(ROOT, provider=build_provider(), data_dir=str(tmp_path), language="zh-CN")


def test_config_pushed_with_property_keys(qapp, tmp_path) -> None:
    obox = _app(tmp_path)
    sent = []
    obox.bus.send = lambda message: sent.append(message)
    obox._extensions_config = {
        "webapp.chenzhi": {
            "profileRoot": {"type": "string", "default": ""},
            "limitMb": {"type": "enum", "default": "2048"},
        }
    }
    obox._settings["webapp.chenzhi.limitMb"] = "512"
    obox._push_extension_configs()
    assert len(sent) == 1
    message = sent[0]
    assert message.dst == "webapp.chenzhi"
    assert message.payload["values"] == {"profileRoot": "", "limitMb": "512"}
    assert message.payload["defaults"] == {"profileRoot": "", "limitMb": "2048"}
    obox.shutdown()
