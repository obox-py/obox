"""组件状态名；取值参考 HTML 元素的可观测状态。"""

VALUE = "value"
CHECKED = "checked"
SELECTED = "selected"
TEXT = "text"
VISIBLE = "visible"
ENABLED = "enabled"
FOCUSED = "focused"
HOVERED = "hovered"
READONLY = "readonly"
DATA = "data"
CODE = "code"
TITLE = "title"

ALL_STATES = frozenset(
    {
        VALUE,
        CHECKED,
        SELECTED,
        TEXT,
        VISIBLE,
        ENABLED,
        FOCUSED,
        HOVERED,
        READONLY,
        DATA,
        CODE,
        TITLE,
    }
)
