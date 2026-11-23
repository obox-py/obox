"""OML 视图文件：只允许 obox 组件语法，按扩展目录相对路径读取。"""

from __future__ import annotations

from pathlib import Path

OML_SUFFIX = ".oml"


class OmlError(Exception):
    """OML 路径或内容不合法。"""


def is_oml(source: str) -> bool:
    return bool(source) and source.strip().lower().endswith(OML_SUFFIX)


def load_oml(directory: Path, relative: str) -> str:
    """读取扩展目录下的 .oml；拒绝越界路径与缺失文件。"""
    if not is_oml(relative):
        raise OmlError(f"不是 oml 文件：{relative}")
    base = directory.resolve()
    target = (base / relative).resolve()
    if base not in target.parents:
        raise OmlError(f"oml 路径越出扩展目录：{relative}")
    if not target.is_file():
        raise OmlError(f"oml 文件不存在：{relative}")
    return target.read_text(encoding="utf-8")
