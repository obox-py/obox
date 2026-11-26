"""图标工具：把任意 SVG 渲染成单色图标。"""

from __future__ import annotations

from pathlib import Path

from obox.qt import Qt
from obox.qt import QColor, QIcon, QImage, QPainter, QPixmap
from obox.qt import QSvgRenderer


def tinted_pixmap(path: str | Path, color: str, size: int = 44) -> QPixmap:
    """按 alpha 蒙版把 SVG 重染成单色；彩色图标会变成剪影。"""
    renderer = QSvgRenderer(str(path))
    source = QImage(size, size, QImage.Format.Format_ARGB32)
    source.fill(Qt.GlobalColor.transparent)
    painter = QPainter(source)
    renderer.render(painter)
    painter.end()

    tinted = QImage(size, size, QImage.Format.Format_ARGB32)
    tinted.fill(Qt.GlobalColor.transparent)
    painter = QPainter(tinted)
    painter.drawImage(0, 0, source)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(tinted.rect(), QColor(color))
    painter.end()
    return QPixmap.fromImage(tinted)


def tinted_icon(path: str | Path, color: str, size: int = 44) -> QIcon:
    return QIcon(tinted_pixmap(path, color, size))
