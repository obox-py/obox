"""OML 路径解析与越界保护。"""

from __future__ import annotations

from pathlib import Path

import pytest

from obox.oml import OmlError, is_oml, load_oml


def test_load_oml(tmp_path: Path) -> None:
    views = tmp_path / "views"
    views.mkdir()
    (views / "main.oml").write_text('<Div id="root"></Div>', encoding="utf-8")
    assert is_oml("views/main.oml")
    assert "root" in load_oml(tmp_path, "views/main.oml")


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(OmlError):
        load_oml(tmp_path, "views/none.oml")


def test_traversal_rejected(tmp_path: Path) -> None:
    outside = tmp_path.parent / "secret.oml"
    outside.write_text("secret", encoding="utf-8")
    with pytest.raises(OmlError):
        load_oml(tmp_path, "../secret.oml")


def test_suffix_required(tmp_path: Path) -> None:
    (tmp_path / "main.html").write_text("<Div></Div>", encoding="utf-8")
    assert not is_oml("main.html")
    with pytest.raises(OmlError):
        load_oml(tmp_path, "main.html")
