"""关闭行为的纯决策：与 UI 解耦，便于测试。"""

from __future__ import annotations

CLOSE_ACTIONS = ("ask", "tray", "quit")
_CLOSE_CHOICES = ("tray", "quit", "cancel")


def decide_close(action: str, choice: str | None = None, remember: bool = False) -> tuple[str, str | None]:
    """返回 (最终动作, 需要持久化的值)。

    最终动作：tray / quit / cancel；持久化值为 tray 或 quit，None 表示不写。
    """
    if action not in CLOSE_ACTIONS:
        action = "ask"
    if action == "tray":
        return "tray", None
    if action == "quit":
        return "quit", None
    if choice == "cancel" or choice not in _CLOSE_CHOICES:
        return "cancel", None
    persisted = choice if remember else None
    return choice, persisted
