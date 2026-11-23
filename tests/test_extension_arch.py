"""oix 架构判定与安装筛选。"""

from __future__ import annotations

from unittest import mock

from obox.extensions.loader import arch_matches, current_arch, package_arch


def test_package_arch() -> None:
    assert package_arch("rdp-1.0.0-win-x64.oix") == "x64"
    assert package_arch("rdp-1.0.0-WIN-ARM64.oix") == "arm64"
    assert package_arch("rdp-1.0.0.oix") == ""


def test_arch_matches() -> None:
    assert arch_matches("demo.oix")
    with mock.patch("obox.extensions.loader.platform.machine", return_value="AMD64"):
        assert current_arch() == "x64"
        assert arch_matches("rdp-1.0.0-win-x64.oix")
        assert not arch_matches("rdp-1.0.0-win-arm64.oix")
    with mock.patch("obox.extensions.loader.platform.machine", return_value="ARM64"):
        assert current_arch() == "arm64"
        assert arch_matches("rdp-1.0.0-win-arm64.oix")
        assert not arch_matches("rdp-1.0.0-win-x64.oix")
