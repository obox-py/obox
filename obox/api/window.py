"""window 命名空间：消息标识、选项 dataclass 与消息构造函数。

每个函数第一个参数是扩展上下文 ctx，返回一条发往 obox 的 Message，调用方用
ctx.request(...) 取结果。payload 顶层固定带 window_id（发起窗口，可为 None），
宿主据此决定模态框的父窗口；发起扩展由 message.src 标识。

payload 必须能 JSON 序列化：选项里的回调（如 InputBoxOptions.validateInput）在 payload
里为 None，函数参数里的 task / listener 由扩展运行时在进程内执行。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import TYPE_CHECKING, Any

from .message import OB_BOX, Message

if TYPE_CHECKING:
    from ..extensions.context import OboxContext

WINDOW_SHOW_INFORMATION_MSG = "WINDOW_SHOW_INFORMATION_MSG"
WINDOW_SHOW_WARNING_MSG = "WINDOW_SHOW_WARNING_MSG"
WINDOW_SHOW_ERROR_MSG = "WINDOW_SHOW_ERROR_MSG"
WINDOW_SHOW_MESSAGE_BOX_MSG = "WINDOW_SHOW_MESSAGE_BOX_MSG"
WINDOW_SHOW_QUICK_PICK_MSG = "WINDOW_SHOW_QUICK_PICK_MSG"
WINDOW_SHOW_INPUT_BOX_MSG = "WINDOW_SHOW_INPUT_BOX_MSG"
WINDOW_SHOW_OPEN_DIALOG_MSG = "WINDOW_SHOW_OPEN_DIALOG_MSG"
WINDOW_SHOW_SAVE_DIALOG_MSG = "WINDOW_SHOW_SAVE_DIALOG_MSG"
WINDOW_CREATE_MSG = "WINDOW_CREATE_MSG"
WINDOW_CLOSE_MSG = "WINDOW_CLOSE_MSG"
WINDOW_SET_TITLE_MSG = "WINDOW_SET_TITLE_MSG"
WINDOW_GET_ACTIVE_MSG = "WINDOW_GET_ACTIVE_MSG"
WINDOW_LIST_MSG = "WINDOW_LIST_MSG"
WINDOW_FOCUS_MSG = "WINDOW_FOCUS_MSG"
WINDOW_CREATE_STATUS_BAR_ITEM_MSG = "WINDOW_CREATE_STATUS_BAR_ITEM_MSG"
WINDOW_UPDATE_STATUS_BAR_ITEM_MSG = "WINDOW_UPDATE_STATUS_BAR_ITEM_MSG"
WINDOW_DISPOSE_STATUS_BAR_ITEM_MSG = "WINDOW_DISPOSE_STATUS_BAR_ITEM_MSG"
WINDOW_PROGRESS_MSG = "WINDOW_PROGRESS_MSG"
WINDOW_CREATE_OUTPUT_CHANNEL_MSG = "WINDOW_CREATE_OUTPUT_CHANNEL_MSG"
WINDOW_ACTIVE_COLOR_THEME_MSG = "WINDOW_ACTIVE_COLOR_THEME_MSG"
WINDOW_COLOR_THEME_CHANGED_MSG = "WINDOW_COLOR_THEME_CHANGED_MSG"

MESSAGE_BOX_TYPES = ("info", "warning", "error", "question")
STATUS_BAR_ALIGNMENTS = ("left", "right")
DEFAULT_BUTTON = "确定"


@dataclass
class MessageBoxOptions:
    type: str = "info"
    title: str = ""
    message: str = ""
    detail: str = ""
    buttons: list[str] = field(default_factory=lambda: [DEFAULT_BUTTON])
    defaultId: int = 0
    cancelId: int | None = None
    checkboxLabel: str = ""
    modal: bool = True
    parent: str | None = None


@dataclass
class QuickPickOptions:
    placeHolder: str = ""
    canPickMany: bool = False
    ignoreFocusOut: bool = False
    matchOnDescription: bool = False
    title: str = ""


@dataclass
class InputBoxOptions:
    title: str = ""
    prompt: str = ""
    value: str = ""
    placeHolder: str = ""
    password: bool = False
    ignoreFocusOut: bool = False
    validateInput: Callable[[str], str | None] | None = None


@dataclass
class OpenDialogOptions:
    title: str = ""
    defaultUri: str = ""
    canSelectFiles: bool = True
    canSelectFolders: bool = False
    canSelectMany: bool = False
    filters: dict[str, list[str]] = field(default_factory=dict)
    openLabel: str = ""


@dataclass
class SaveDialogOptions:
    title: str = ""
    defaultUri: str = ""
    filters: dict[str, list[str]] = field(default_factory=dict)
    saveLabel: str = ""


@dataclass
class WindowOptions:
    title: str = ""
    oml: str = ""
    html: str = ""
    width: int = 720
    height: int = 520
    parent: str | None = None
    modal: bool = False
    singleton: str = ""


_MESSAGE_BOX_DEFAULTS = asdict(MessageBoxOptions())
_QUICK_PICK_DEFAULTS = asdict(QuickPickOptions())
_INPUT_BOX_DEFAULTS = asdict(InputBoxOptions())
_OPEN_DIALOG_DEFAULTS = asdict(OpenDialogOptions())
_SAVE_DIALOG_DEFAULTS = asdict(SaveDialogOptions())
_WINDOW_DEFAULTS = asdict(WindowOptions())


def _wire(value: Any) -> Any:
    """去掉回调：payload 跨进程序列化，回调由扩展运行时在进程内接管。"""
    if isinstance(value, Mapping):
        return {str(key): _wire(item) for key, item in value.items() if not callable(item)}
    if isinstance(value, (list, tuple)):
        return [_wire(item) for item in value if not callable(item)]
    return value


def _options(options: Any) -> dict[str, Any]:
    if options is None:
        return {}
    if is_dataclass(options) and not isinstance(options, type):
        return _wire(asdict(options))
    if isinstance(options, Mapping):
        return _wire(dict(options))
    raise TypeError(f"options 必须是 dataclass 或字典：{type(options).__name__}")


def _merged(options: Any, defaults: dict[str, Any], label: str) -> dict[str, Any]:
    data = dict(defaults)
    data.update(_options(options))
    unknown = sorted(set(data) - set(defaults))
    if unknown:
        raise ValueError(f"{label} 含未知字段：{', '.join(unknown)}")
    return data


def _request(ctx: OboxContext, msg_id: str, payload: dict[str, Any] | None = None) -> Message:
    data: dict[str, Any] = {"window_id": ctx.window_id}
    data.update(_wire(payload or {}))
    return Message(src=ctx.extension_id, dst=OB_BOX, msg_id=msg_id, payload=data)


def _window_id(windowId: Any) -> str:
    value = str(windowId or "").strip()
    if not value:
        raise ValueError("windowId 不能为空")
    return value


def _item_id(itemId: Any) -> str:
    value = str(itemId or "").strip()
    if not value:
        raise ValueError("itemId 不能为空")
    return value


def _dialog_filters(filters: Any) -> dict[str, list[str]]:
    if not filters:
        return {}
    if not isinstance(filters, Mapping):
        raise TypeError("filters 必须是 {名称: [后缀]} 的字典")
    result: dict[str, list[str]] = {}
    for name, values in filters.items():
        if isinstance(values, str):
            values = [values]
        result[str(name)] = [str(item) for item in (values or [])]
    return result


def _message_box_options(options: Any) -> dict[str, Any]:
    data = _merged(options, _MESSAGE_BOX_DEFAULTS, "MessageBoxOptions")
    kind = str(data["type"] or "info")
    if kind not in MESSAGE_BOX_TYPES:
        raise ValueError(f"MessageBoxOptions.type 只能是 {'/'.join(MESSAGE_BOX_TYPES)}：{kind!r}")
    data["type"] = kind
    data["buttons"] = [str(item) for item in data["buttons"] or []] or [DEFAULT_BUTTON]
    data["defaultId"] = int(data["defaultId"])
    if data["cancelId"] is not None:
        data["cancelId"] = int(data["cancelId"])
    data["checkboxLabel"] = str(data["checkboxLabel"])
    data["modal"] = bool(data["modal"])
    data["parent"] = None if data["parent"] in (None, "") else str(data["parent"])
    return data


def _quick_pick_items(items: Iterable[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in items or ():
        if isinstance(item, str):
            result.append({"label": item})
            continue
        if isinstance(item, Mapping) and str(item.get("label") or "").strip():
            result.append(_wire(dict(item)))
            continue
        raise TypeError("QuickPick 项必须是字符串或带 label 的字典")
    return result


def _quick_pick_options(options: Any) -> dict[str, Any]:
    data = _merged(options, _QUICK_PICK_DEFAULTS, "QuickPickOptions")
    for key in ("canPickMany", "ignoreFocusOut", "matchOnDescription"):
        data[key] = bool(data[key])
    for key in ("placeHolder", "title"):
        data[key] = str(data[key])
    return data


def _input_box_options(options: Any) -> dict[str, Any]:
    data = _merged(options, _INPUT_BOX_DEFAULTS, "InputBoxOptions")
    for key in ("password", "ignoreFocusOut"):
        data[key] = bool(data[key])
    for key in ("title", "prompt", "value", "placeHolder"):
        data[key] = str(data[key])
    return data


def _open_dialog_options(options: Any) -> dict[str, Any]:
    data = _merged(options, _OPEN_DIALOG_DEFAULTS, "OpenDialogOptions")
    files, folders = bool(data["canSelectFiles"]), bool(data["canSelectFolders"])
    if not files and not folders:
        raise ValueError("canSelectFiles 与 canSelectFolders 至少一个为真")
    data.update(
        {
            "canSelectFiles": files,
            "canSelectFolders": folders,
            "canSelectMany": bool(data["canSelectMany"]),
            "filters": _dialog_filters(data["filters"]),
            "title": str(data["title"]),
            "defaultUri": str(data["defaultUri"]),
            "openLabel": str(data["openLabel"]),
        }
    )
    return data


def _save_dialog_options(options: Any) -> dict[str, Any]:
    data = _merged(options, _SAVE_DIALOG_DEFAULTS, "SaveDialogOptions")
    data.update(
        {
            "filters": _dialog_filters(data["filters"]),
            "title": str(data["title"]),
            "defaultUri": str(data["defaultUri"]),
            "saveLabel": str(data["saveLabel"]),
        }
    )
    return data


def _window_options(options: Any) -> dict[str, Any]:
    data = _merged(options, _WINDOW_DEFAULTS, "WindowOptions")
    try:
        width, height = int(data["width"]), int(data["height"])
    except (TypeError, ValueError):
        raise ValueError("WindowOptions.width/height 必须是整数") from None
    if width <= 0 or height <= 0:
        raise ValueError("WindowOptions.width/height 必须为正数")
    data.update(
        {
            "width": width,
            "height": height,
            "modal": bool(data["modal"]),
            "title": str(data["title"]),
            "oml": str(data["oml"]),
            "html": str(data["html"]),
            "singleton": str(data["singleton"]),
            "parent": None if data["parent"] in (None, "") else str(data["parent"]),
        }
    )
    return data


def _notice(
    ctx: OboxContext,
    msg_id: str,
    kind: str,
    message: str,
    items: Iterable[Any],
    options: Any,
) -> Message:
    return _request(
        ctx,
        msg_id,
        {
            "type": kind,
            "message": str(message),
            "items": [str(item) for item in items],
            "options": _options(options),
        },
    )


def showInformationMessage(
    ctx: OboxContext, message: str, *items: str, options: dict[str, Any] | None = None
) -> Message:
    return _notice(ctx, WINDOW_SHOW_INFORMATION_MSG, "info", message, items, options)


def showWarningMessage(
    ctx: OboxContext, message: str, *items: str, options: dict[str, Any] | None = None
) -> Message:
    return _notice(ctx, WINDOW_SHOW_WARNING_MSG, "warning", message, items, options)


def showErrorMessage(
    ctx: OboxContext, message: str, *items: str, options: dict[str, Any] | None = None
) -> Message:
    return _notice(ctx, WINDOW_SHOW_ERROR_MSG, "error", message, items, options)


def showMessageBox(
    ctx: OboxContext, options: MessageBoxOptions | dict[str, Any] | None = None
) -> Message:
    return _request(ctx, WINDOW_SHOW_MESSAGE_BOX_MSG, {"options": _message_box_options(options)})


def showQuickPick(
    ctx: OboxContext,
    items: Iterable[str | dict[str, Any]],
    options: QuickPickOptions | dict[str, Any] | None = None,
) -> Message:
    return _request(
        ctx,
        WINDOW_SHOW_QUICK_PICK_MSG,
        {"items": _quick_pick_items(items), "options": _quick_pick_options(options)},
    )


def showInputBox(
    ctx: OboxContext, options: InputBoxOptions | dict[str, Any] | None = None
) -> Message:
    return _request(ctx, WINDOW_SHOW_INPUT_BOX_MSG, {"options": _input_box_options(options)})


def showOpenDialog(
    ctx: OboxContext, options: OpenDialogOptions | dict[str, Any] | None = None
) -> Message:
    return _request(ctx, WINDOW_SHOW_OPEN_DIALOG_MSG, {"options": _open_dialog_options(options)})


def showSaveDialog(
    ctx: OboxContext, options: SaveDialogOptions | dict[str, Any] | None = None
) -> Message:
    return _request(ctx, WINDOW_SHOW_SAVE_DIALOG_MSG, {"options": _save_dialog_options(options)})


def createWindow(ctx: OboxContext, options: WindowOptions | dict[str, Any] | None = None) -> Message:
    return _request(ctx, WINDOW_CREATE_MSG, {"options": _window_options(options)})


def closeWindow(ctx: OboxContext, windowId: str) -> Message:
    return _request(ctx, WINDOW_CLOSE_MSG, {"windowId": _window_id(windowId)})


def setWindowTitle(ctx: OboxContext, windowId: str, title: str) -> Message:
    return _request(
        ctx, WINDOW_SET_TITLE_MSG, {"windowId": _window_id(windowId), "title": str(title)}
    )


def getActiveWindow(ctx: OboxContext) -> Message:
    return _request(ctx, WINDOW_GET_ACTIVE_MSG)


def listWindows(ctx: OboxContext) -> Message:
    return _request(ctx, WINDOW_LIST_MSG)


def focusWindow(ctx: OboxContext, windowId: str) -> Message:
    return _request(ctx, WINDOW_FOCUS_MSG, {"windowId": _window_id(windowId)})


def createStatusBarItem(
    ctx: OboxContext, alignment: str = "left", priority: int = 0
) -> Message:
    side = str(alignment or "left").strip().lower()
    if side not in STATUS_BAR_ALIGNMENTS:
        raise ValueError(f"alignment 只能是 left 或 right：{alignment!r}")
    return _request(
        ctx,
        WINDOW_CREATE_STATUS_BAR_ITEM_MSG,
        {"alignment": side, "priority": int(priority)},
    )


def updateStatusBarItem(
    ctx: OboxContext,
    itemId: str,
    *,
    text: str | None = None,
    tooltip: str | None = None,
    command: str | None = None,
    show: bool | None = None,
) -> Message:
    """更新状态栏项的文本/提示/命令，show 控制显示与隐藏。"""
    payload: dict[str, Any] = {"itemId": _item_id(itemId)}
    if text is not None:
        payload["text"] = str(text)
    if tooltip is not None:
        payload["tooltip"] = str(tooltip)
    if command is not None:
        payload["command"] = str(command)
    if show is not None:
        payload["show"] = bool(show)
    return _request(ctx, WINDOW_UPDATE_STATUS_BAR_ITEM_MSG, payload)


def disposeStatusBarItem(ctx: OboxContext, itemId: str) -> Message:
    return _request(ctx, WINDOW_DISPOSE_STATUS_BAR_ITEM_MSG, {"itemId": _item_id(itemId)})


def withProgress(
    ctx: OboxContext,
    options: dict[str, Any] | None = None,
    task: Callable[..., Any] | None = None,
) -> Message:
    """构造“开始进度”消息；task 由调用方在扩展进程内执行，不进入 payload。"""
    if task is not None and not callable(task):
        raise TypeError("task 必须是可调用对象")
    data = _options(options)
    return _request(
        ctx,
        WINDOW_PROGRESS_MSG,
        {"options": data, "cancellable": bool(data.get("cancellable", False))},
    )


def createOutputChannel(
    ctx: OboxContext, name: str, options: dict[str, Any] | None = None
) -> Message:
    channel = str(name or "").strip()
    if not channel:
        raise ValueError("输出通道名不能为空")
    return _request(
        ctx, WINDOW_CREATE_OUTPUT_CHANNEL_MSG, {"name": channel, "options": _options(options)}
    )


def activeColorTheme(ctx: OboxContext) -> Message:
    return _request(ctx, WINDOW_ACTIVE_COLOR_THEME_MSG)


def onDidChangeActiveColorTheme(
    ctx: OboxContext, listener: Callable[[dict[str, Any]], None] | None = None
) -> Message:
    if listener is not None and not callable(listener):
        raise TypeError("listener 必须是可调用对象")
    return _request(ctx, WINDOW_COLOR_THEME_CHANGED_MSG, {"subscribe": True})


__all__ = [
    "DEFAULT_BUTTON",
    "InputBoxOptions",
    "MESSAGE_BOX_TYPES",
    "MessageBoxOptions",
    "OpenDialogOptions",
    "QuickPickOptions",
    "STATUS_BAR_ALIGNMENTS",
    "SaveDialogOptions",
    "WINDOW_ACTIVE_COLOR_THEME_MSG",
    "WINDOW_CLOSE_MSG",
    "WINDOW_COLOR_THEME_CHANGED_MSG",
    "WINDOW_CREATE_MSG",
    "WINDOW_CREATE_OUTPUT_CHANNEL_MSG",
    "WINDOW_CREATE_STATUS_BAR_ITEM_MSG",
    "WINDOW_DISPOSE_STATUS_BAR_ITEM_MSG",
    "WINDOW_FOCUS_MSG",
    "WINDOW_GET_ACTIVE_MSG",
    "WINDOW_LIST_MSG",
    "WINDOW_PROGRESS_MSG",
    "WINDOW_SET_TITLE_MSG",
    "WINDOW_SHOW_ERROR_MSG",
    "WINDOW_SHOW_INFORMATION_MSG",
    "WINDOW_SHOW_INPUT_BOX_MSG",
    "WINDOW_SHOW_MESSAGE_BOX_MSG",
    "WINDOW_SHOW_OPEN_DIALOG_MSG",
    "WINDOW_SHOW_QUICK_PICK_MSG",
    "WINDOW_SHOW_SAVE_DIALOG_MSG",
    "WINDOW_SHOW_WARNING_MSG",
    "WINDOW_UPDATE_STATUS_BAR_ITEM_MSG",
    "WindowOptions",
    "activeColorTheme",
    "closeWindow",
    "createOutputChannel",
    "disposeStatusBarItem",
    "createStatusBarItem",
    "createWindow",
    "focusWindow",
    "getActiveWindow",
    "listWindows",
    "onDidChangeActiveColorTheme",
    "setWindowTitle",
    "showErrorMessage",
    "showInformationMessage",
    "showInputBox",
    "showMessageBox",
    "showOpenDialog",
    "showQuickPick",
    "showSaveDialog",
    "showWarningMessage",
    "updateStatusBarItem",
    "withProgress",
]