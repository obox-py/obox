"""组件事件名；与 antd 的事件语义对齐，统一用 kebab-case。"""

CLICK = "click"
DOUBLE_CLICK = "dblclick"
CONTEXT_MENU = "contextmenu"
MOUSE_ENTER = "mouseenter"
MOUSE_LEAVE = "mouseleave"
MOUSE_MOVE = "mousemove"
KEY_DOWN = "keydown"
KEY_UP = "keyup"
INPUT = "input"
CHANGE = "change"
CHECKED_CHANGE = "checkedchange"
FOCUS = "focus"
BLUR = "blur"
DRAG_START = "dragstart"
DRAG = "drag"
DRAG_END = "dragend"
DROP = "drop"
CLOSE = "close"

ALL_EVENTS = frozenset(
    {
        CLICK,
        DOUBLE_CLICK,
        CONTEXT_MENU,
        MOUSE_ENTER,
        MOUSE_LEAVE,
        MOUSE_MOVE,
        KEY_DOWN,
        KEY_UP,
        INPUT,
        CHANGE,
        CHECKED_CHANGE,
        FOCUS,
        BLUR,
        DRAG_START,
        DRAG,
        DRAG_END,
        DROP,
        CLOSE,
    }
)
