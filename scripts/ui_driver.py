"""UI 驱动小工具：等待、鼠标点击、键盘输入、截图与日志。"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PICS_DIR = PROJECT_ROOT / "tmp" / "pics"
LOGS_DIR = PROJECT_ROOT / "tmp" / "logs"


def setup_logging(name: str) -> logging.Logger:
    """日志同时写文件与标准错误，便于 CI 与人工排查。"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(LOGS_DIR / f"{name}_{stamp}.log", encoding="utf-8")
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    for handler in (file_handler, stream_handler):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


class UiDriver:
    """把常用的界面操作收敛到一处，场景脚本只表达意图。"""

    def __init__(self, logger: logging.Logger) -> None:
        self.log = logger
        PICS_DIR.mkdir(parents=True, exist_ok=True)

    def wait_until(self, predicate, timeout: float = 10.0, interval: float = 0.05) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return True
            QTest.qWait(int(interval * 1000))
        return False

    def click(self, widget: QWidget) -> None:
        self.log.info("点击 %s", widget.objectName())
        QTest.mouseClick(widget, Qt.MouseButton.LeftButton)

    def type_text(self, widget: QWidget, text: str) -> None:
        self.log.info("向 %s 输入 %r", widget.objectName(), text)
        widget.setFocus()
        QTest.keyClicks(widget, text)

    def screenshot(self, widget: QWidget, name: str) -> Path:
        QTest.qWait(150)  # 等一帧重绘，否则切换视图后立刻抓图会漏掉图标
        target = PICS_DIR / f"{name}.png"
        widget.grab().save(str(target), "PNG")
        self.log.info("截图 %s", target)
        return target
