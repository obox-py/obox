"""window / commands / env / extensions 消息构造，以及状态栏与输出面板。"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from obox.api import commands, env, extensions, window
from obox.api.message import OB_BOX, Message
from obox.qt import QFrame, QLabel
from obox.ui import palette
from obox.ui.output_panel import OutputPanel
from obox.ui.statusbar import StatusBar


def make_ctx(window_id: str | None = "w-1") -> Any:
    return SimpleNamespace(extension_id="demo.obox", window_id=window_id)


def assert_envelope(message: Message, msg_id: str, dst: str) -> dict[str, Any]:
    assert isinstance(message, Message)
    assert message.msg_id == msg_id
    assert message.src == "demo.obox"
    assert message.dst == dst
    assert message.reply is False
    assert message.correlation_id == ""
    return message.payload


def assert_request(
    message: Message, msg_id: str, window_id: str | None = "w-1"
) -> dict[str, Any]:
    """window 命名空间：发往 obox，并带发起窗口。"""
    payload = assert_envelope(message, msg_id, OB_BOX)
    assert payload["window_id"] == window_id
    return payload


# ---------- window：通知 ----------
def test_notice_messages_share_envelope() -> None:
    ctx = make_ctx()
    cases = (
        (window.showInformationMessage, window.WINDOW_SHOW_INFORMATION_MSG, "info"),
        (window.showWarningMessage, window.WINDOW_SHOW_WARNING_MSG, "warning"),
        (window.showErrorMessage, window.WINDOW_SHOW_ERROR_MSG, "error"),
    )
    for function, msg_id, kind in cases:
        payload = assert_request(function(ctx, "备份完成", "打开", "关闭"), msg_id)
        assert payload["type"] == kind
        assert payload["message"] == "备份完成"
        assert payload["items"] == ["打开", "关闭"]
        assert payload["options"] == {}


def test_notice_forwards_options_and_carries_window_id() -> None:
    payload = assert_request(
        window.showWarningMessage(make_ctx(), "磁盘快满", options={"modal": False}), 
        window.WINDOW_SHOW_WARNING_MSG,
    )
    assert payload["options"] == {"modal": False}
    assert payload["items"] == []
    payload = assert_request(
        window.showInformationMessage(make_ctx(None), "主窗口"),
        window.WINDOW_SHOW_INFORMATION_MSG,
        window_id=None,
    )
    assert payload["window_id"] is None


# ---------- window：模态框 ----------
def test_message_box_defaults() -> None:
    options = assert_request(window.showMessageBox(make_ctx()), window.WINDOW_SHOW_MESSAGE_BOX_MSG)[
        "options"
    ]
    assert options["type"] == "info"
    assert options["buttons"] == ["确定"]
    assert options["defaultId"] == 0
    assert options["cancelId"] is None
    assert options["checkboxLabel"] == ""
    assert options["modal"] is True
    assert options["parent"] is None


def test_message_box_accepts_dataclass_and_partial_dict() -> None:
    ctx = make_ctx()
    box = window.MessageBoxOptions(
        type="warning",
        title="确认",
        message="继续？",
        detail="不可撤销",
        buttons=["继续", "取消"],
        defaultId=0,
        cancelId=1,
        checkboxLabel="记住",
        modal=False,
        parent="w-1",
    )
    options = assert_request(window.showMessageBox(ctx, box), window.WINDOW_SHOW_MESSAGE_BOX_MSG)[
        "options"
    ]
    assert options["type"] == "warning"
    assert options["detail"] == "不可撤销"
    assert options["buttons"] == ["继续", "取消"]
    assert options["cancelId"] == 1
    assert options["checkboxLabel"] == "记住"
    assert options["modal"] is False
    assert options["parent"] == "w-1"

    partial = assert_request(
        window.showMessageBox(ctx, {"type": "question", "message": "保存？"}),
        window.WINDOW_SHOW_MESSAGE_BOX_MSG,
    )["options"]
    assert partial["type"] == "question"
    assert partial["message"] == "保存？"
    assert partial["buttons"] == ["确定"]


def test_message_box_rejects_bad_type_and_unknown_fields() -> None:
    with pytest.raises(ValueError, match="type"):
        window.showMessageBox(make_ctx(), {"type": "fatal"})
    with pytest.raises(ValueError, match="未知字段"):
        window.showMessageBox(make_ctx(), {"colour": "red"})
    with pytest.raises(TypeError):
        window.showMessageBox(make_ctx(), ["info"])


# ---------- window：quickPick / inputBox ----------
def test_quick_pick_normalizes_items_and_options() -> None:
    payload = assert_request(
        window.showQuickPick(
            make_ctx(),
            ["甲", {"label": "乙", "description": "描述", "detail": "细节"}],
            window.QuickPickOptions(canPickMany=True, title="选一个"),
        ),
        window.WINDOW_SHOW_QUICK_PICK_MSG,
    )
    assert payload["items"] == [
        {"label": "甲"},
        {"label": "乙", "description": "描述", "detail": "细节"},
    ]
    options = payload["options"]
    assert options["canPickMany"] is True
    assert options["title"] == "选一个"
    assert options["placeHolder"] == ""
    assert options["ignoreFocusOut"] is False


def test_quick_pick_rejects_items_without_label() -> None:
    with pytest.raises(TypeError, match="label"):
        window.showQuickPick(make_ctx(), [{"description": "缺 label"}])
    with pytest.raises(TypeError):
        window.showQuickPick(make_ctx(), [42])
    assert assert_request(window.showQuickPick(make_ctx(), []), window.WINDOW_SHOW_QUICK_PICK_MSG)[
        "items"
    ] == []


def test_input_box_options_stay_json_safe() -> None:
    def validate(value: str) -> str | None:
        return None if value else "必填"

    box = window.InputBoxOptions(
        title="名字", prompt="输入名字", value="demo", placeHolder="项目名", password=True
    )
    box.validateInput = validate
    options = assert_request(window.showInputBox(make_ctx(), box), window.WINDOW_SHOW_INPUT_BOX_MSG)[
        "options"
    ]
    assert options["title"] == "名字"
    assert options["prompt"] == "输入名字"
    assert options["value"] == "demo"
    assert options["placeHolder"] == "项目名"
    assert options["password"] is True
    assert options["validateInput"] is None
    json.dumps(options)


# ---------- window：打开/保存对话框 ----------
def test_open_dialog_defaults_and_filters() -> None:
    defaults = assert_request(window.showOpenDialog(make_ctx()), window.WINDOW_SHOW_OPEN_DIALOG_MSG)[
        "options"
    ]
    assert defaults["canSelectFiles"] is True
    assert defaults["canSelectFolders"] is False
    assert defaults["canSelectMany"] is False

    options = assert_request(
        window.showOpenDialog(
            make_ctx(),
            {
                "title": "选目录",
                "canSelectFiles": False,
                "canSelectFolders": True,
                "canSelectMany": True,
                "filters": {"文本": ["txt", ".md"]},
                "openLabel": "打开",
            },
        ),
        window.WINDOW_SHOW_OPEN_DIALOG_MSG,
    )["options"]
    assert options["canSelectFiles"] is False
    assert options["canSelectFolders"] is True
    assert options["canSelectMany"] is True
    assert options["filters"] == {"文本": ["txt", ".md"]}
    assert options["openLabel"] == "打开"


def test_open_dialog_needs_a_selection_target() -> None:
    with pytest.raises(ValueError, match="canSelectFiles"):
        window.showOpenDialog(make_ctx(), {"canSelectFiles": False})


def test_save_dialog_options() -> None:
    options = assert_request(
        window.showSaveDialog(
            make_ctx(), window.SaveDialogOptions(saveLabel="保存", defaultUri="~/note.txt")
        ),
        window.WINDOW_SHOW_SAVE_DIALOG_MSG,
    )["options"]
    assert options["saveLabel"] == "保存"
    assert options["defaultUri"] == "~/note.txt"
    assert options["filters"] == {}


# ---------- window：窗口 ----------
def test_create_window_defaults_and_validation() -> None:
    options = assert_request(window.createWindow(make_ctx()), window.WINDOW_CREATE_MSG)["options"]
    assert options == {
        "title": "",
        "oml": "",
        "html": "",
        "width": 720,
        "height": 520,
        "parent": None,
        "modal": False,
        "singleton": "",
    }
    custom = assert_request(
        window.createWindow(
            make_ctx(),
            window.WindowOptions(
                title="详情", oml="views/detail.oml", width=400, height=300, singleton="detail", modal=True
            ),
        ),
        window.WINDOW_CREATE_MSG,
    )["options"]
    assert custom["title"] == "详情"
    assert custom["oml"] == "views/detail.oml"
    assert custom["width"] == 400 and custom["height"] == 300
    assert custom["singleton"] == "detail"
    assert custom["modal"] is True

    with pytest.raises(ValueError, match="正数"):
        window.createWindow(make_ctx(), {"width": 0})
    with pytest.raises(ValueError, match="整数"):
        window.createWindow(make_ctx(), {"height": "tall"})


def test_window_controls_carry_window_id() -> None:
    ctx = make_ctx()
    assert assert_request(window.closeWindow(ctx, "w-9"), window.WINDOW_CLOSE_MSG)["windowId"] == "w-9"
    title = assert_request(window.setWindowTitle(ctx, "w-9", "标题"), window.WINDOW_SET_TITLE_MSG)
    assert title["windowId"] == "w-9" and title["title"] == "标题"
    assert assert_request(window.focusWindow(ctx, "w-9"), window.WINDOW_FOCUS_MSG)["windowId"] == "w-9"


def test_window_lookup_messages_only_carry_window_id() -> None:
    for function, msg_id in (
        (window.getActiveWindow, window.WINDOW_GET_ACTIVE_MSG),
        (window.listWindows, window.WINDOW_LIST_MSG),
    ):
        payload = assert_request(function(make_ctx()), msg_id)
        assert set(payload) == {"window_id"}


def test_window_controls_reject_empty_window_id() -> None:
    with pytest.raises(ValueError, match="windowId"):
        window.closeWindow(make_ctx(), "")
    with pytest.raises(ValueError, match="windowId"):
        window.focusWindow(make_ctx(), None)
    with pytest.raises(ValueError, match="windowId"):
        window.setWindowTitle(make_ctx(), "  ", "标题")


# ---------- window：状态栏 / 进度 / 输出 / 主题 ----------
def test_create_status_bar_item_validates_alignment() -> None:
    payload = assert_request(
        window.createStatusBarItem(make_ctx(), "right", 7), window.WINDOW_CREATE_STATUS_BAR_ITEM_MSG
    )
    assert payload["alignment"] == "right"
    assert payload["priority"] == 7
    assert assert_request(
        window.createStatusBarItem(make_ctx()), window.WINDOW_CREATE_STATUS_BAR_ITEM_MSG
    )["alignment"] == "left"
    with pytest.raises(ValueError, match="alignment"):
        window.createStatusBarItem(make_ctx(), "middle")


def test_status_bar_item_update_and_dispose() -> None:
    ctx = make_ctx()
    payload = assert_request(
        window.updateStatusBarItem(
            ctx, "item-1", text="就绪", tooltip="提示", command="demo.run", show=True
        ),
        window.WINDOW_UPDATE_STATUS_BAR_ITEM_MSG,
    )
    assert payload["itemId"] == "item-1"
    assert payload["text"] == "就绪"
    assert payload["tooltip"] == "提示"
    assert payload["command"] == "demo.run"
    assert payload["show"] is True

    partial = assert_request(
        window.updateStatusBarItem(ctx, "item-1", show=False),
        window.WINDOW_UPDATE_STATUS_BAR_ITEM_MSG,
    )
    assert set(partial) == {"window_id", "itemId", "show"}

    disposed = assert_request(
        window.disposeStatusBarItem(ctx, " item-1 "), window.WINDOW_DISPOSE_STATUS_BAR_ITEM_MSG
    )
    assert disposed["itemId"] == "item-1"

    with pytest.raises(ValueError, match="itemId"):
        window.updateStatusBarItem(ctx, "")
    with pytest.raises(ValueError, match="itemId"):
        window.disposeStatusBarItem(ctx, " ")


def test_with_progress_keeps_task_out_of_payload() -> None:
    calls: list[int] = []

    def task(progress: Any, token: Any) -> None:
        calls.append(1)

    payload = assert_request(
        window.withProgress(make_ctx(), {"title": "安装", "cancellable": True}, task),
        window.WINDOW_PROGRESS_MSG,
    )
    assert payload["options"] == {"title": "安装", "cancellable": True}
    assert payload["cancellable"] is True
    assert "task" not in payload
    assert calls == []

    defaults = assert_request(window.withProgress(make_ctx()), window.WINDOW_PROGRESS_MSG)
    assert defaults["options"] == {}
    assert defaults["cancellable"] is False
    with pytest.raises(TypeError, match="task"):
        window.withProgress(make_ctx(), {}, "not-callable")


def test_create_output_channel_validates_name() -> None:
    payload = assert_request(
        window.createOutputChannel(make_ctx(), " demo ", {"log": True}),
        window.WINDOW_CREATE_OUTPUT_CHANNEL_MSG,
    )
    assert payload["name"] == "demo"
    assert payload["options"] == {"log": True}
    with pytest.raises(ValueError, match="通道名"):
        window.createOutputChannel(make_ctx(), " ")


def test_color_theme_messages() -> None:
    assert_request(window.activeColorTheme(make_ctx()), window.WINDOW_ACTIVE_COLOR_THEME_MSG)
    payload = assert_request(
        window.onDidChangeActiveColorTheme(make_ctx(), lambda theme: None),
        window.WINDOW_COLOR_THEME_CHANGED_MSG,
    )
    assert payload["subscribe"] is True
    with pytest.raises(TypeError, match="listener"):
        window.onDidChangeActiveColorTheme(make_ctx(), "bad")


# ---------- commands ----------
def test_register_command_keeps_callback_out_of_payload() -> None:
    def handler(value: Any) -> Any:
        return value

    payload = assert_envelope(
        commands.registerCommand(make_ctx(), "demo.echo", handler, thisArg={"n": 1}),
        commands.COMMANDS_REGISTER_MSG,
        extensions.HOST_ID,
    )
    assert payload["command"] == "demo.echo"
    assert payload["thisArg"] == {"n": 1}
    assert "callback" not in payload
    with pytest.raises(TypeError, match="callback"):
        commands.registerCommand(make_ctx(), "demo.echo", None)
    with pytest.raises(ValueError, match="commandId"):
        commands.registerCommand(make_ctx(), " ", handler)


def test_execute_and_get_commands() -> None:
    ctx = make_ctx()
    payload = assert_envelope(
        commands.executeCommand(ctx, "demo.echo", 1, "a"), commands.COMMANDS_EXECUTE_MSG, extensions.HOST_ID
    )
    assert payload["command"] == "demo.echo"
    assert payload["args"] == [1, "a"]
    assert assert_envelope(
        commands.executeCommand(ctx, "demo.echo"), commands.COMMANDS_EXECUTE_MSG, extensions.HOST_ID
    )["args"] == []
    payload = assert_envelope(commands.getCommands(ctx, True), commands.COMMANDS_GET_MSG, extensions.HOST_ID)
    assert payload["filterInternal"] is True
    assert assert_envelope(
        commands.getCommands(ctx), commands.COMMANDS_GET_MSG, extensions.HOST_ID
    )["filterInternal"] is False
    with pytest.raises(ValueError, match="commandId"):
        commands.executeCommand(ctx, "")


# ---------- env ----------
@pytest.mark.parametrize(
    ("function", "field"),
    (
        (env.appName, "appName"),
        (env.appVersion, "appVersion"),
        (env.language, "language"),
        (env.appHost, "appHost"),
        (env.platform, "platform"),
        (env.arch, "arch"),
    ),
)
def test_env_info_requests(function: Any, field: str) -> None:
    payload = assert_envelope(function(make_ctx()), env.ENV_INFO_MSG, OB_BOX)
    assert payload["property"] == field


def test_clipboard_messages() -> None:
    payload = assert_envelope(env.clipboard.writeText(make_ctx(), "你好"), env.ENV_CLIPBOARD_WRITE_MSG, OB_BOX)
    assert payload["text"] == "你好"
    assert_envelope(env.clipboard.readText(make_ctx()), env.ENV_CLIPBOARD_READ_MSG, OB_BOX)


def test_env_open_messages_require_target() -> None:
    payload = assert_envelope(
        env.openExternal(make_ctx(), " https://example.com "), env.ENV_OPEN_EXTERNAL_MSG, OB_BOX
    )
    assert payload["uri"] == "https://example.com"
    assert assert_envelope(env.openPath(make_ctx(), "/tmp"), env.ENV_OPEN_PATH_MSG, OB_BOX)["path"] == "/tmp"
    with pytest.raises(ValueError, match="uri"):
        env.openExternal(make_ctx(), "")
    with pytest.raises(ValueError, match="path"):
        env.openPath(make_ctx(), "   ")


# ---------- extensions ----------
def test_extensions_namespace_messages() -> None:
    ctx = make_ctx()
    assert_envelope(extensions.all(ctx), extensions.EXTENSIONS_ALL_MSG, extensions.HOST_ID)
    assert assert_envelope(
        extensions.getExtension(ctx, " demo.obox "), extensions.EXTENSIONS_GET_MSG, extensions.HOST_ID
    )["id"] == "demo.obox"
    payload = assert_envelope(
        extensions.onDidChange(ctx, lambda event: None), extensions.EXTENSIONS_ON_CHANGE_MSG, extensions.HOST_ID
    )
    assert payload["subscribe"] is True
    with pytest.raises(ValueError, match="id"):
        extensions.getExtension(ctx, "")
    with pytest.raises(TypeError, match="listener"):
        extensions.onDidChange(ctx, 42)


# ---------- 消息整体可序列化 ----------
def test_messages_are_json_serializable() -> None:
    ctx = make_ctx()
    messages = [
        window.showInformationMessage(ctx, "hi", "好"),
        window.showMessageBox(ctx, window.MessageBoxOptions(message="hi")),
        window.showQuickPick(ctx, ["甲", {"label": "乙", "description": "d"}]),
        window.showInputBox(ctx, window.InputBoxOptions(title="名字")),
        window.showOpenDialog(ctx),
        window.showSaveDialog(ctx),
        window.createWindow(ctx),
        window.closeWindow(ctx, "w-2"),
        window.setWindowTitle(ctx, "w-2", "标题"),
        window.getActiveWindow(ctx),
        window.listWindows(ctx),
        window.focusWindow(ctx, "w-2"),
        window.createStatusBarItem(ctx),
        window.updateStatusBarItem(ctx, "item-1", text="就绪"),
        window.disposeStatusBarItem(ctx, "item-1"),
        window.withProgress(ctx, {"title": "t"}, lambda progress, token: None),
        window.createOutputChannel(ctx, "demo"),
        window.activeColorTheme(ctx),
        window.onDidChangeActiveColorTheme(ctx, lambda theme: None),
        commands.registerCommand(ctx, "demo.run", lambda: None),
        commands.executeCommand(ctx, "demo.run", 1, "a"),
        commands.getCommands(ctx),
        env.appName(ctx),
        env.clipboard.writeText(ctx, "x"),
        env.openExternal(ctx, "https://example.com"),
        env.openPath(ctx, "/tmp"),
        extensions.all(ctx),
        extensions.getExtension(ctx, "demo.obox"),
        extensions.onDidChange(ctx, lambda event: None),
    ]
    for message in messages:
        encoded = json.dumps(message.to_dict(), ensure_ascii=False)
        assert message.msg_id in encoded


# ---------- 状态栏 ----------
def test_status_bar_orders_items_by_priority(qapp: Any) -> None:
    palette.reset()
    bar = StatusBar()
    low = bar.add_item("低", "left", 0)
    high = bar.add_item("高", "left", 10)
    right = bar.add_item("右", "right", 5)
    assert [item.text() for item in bar.items("left")] == ["高", "低"]
    assert bar.items("right") == [right]
    assert bar.items() == [high, right, low]
    bar.deleteLater()


def test_status_bar_item_activates_command(qapp: Any) -> None:
    palette.reset()
    bar = StatusBar()
    fired: list[str] = []
    bar.command_triggered.connect(fired.append)
    item = bar.add_item("刷新", "left", 1, tooltip="刷新列表", command="demo.refresh")
    assert item.command == "demo.refresh"
    assert item.toolTip() == "刷新列表"
    item.activate()
    assert fired == ["demo.refresh"]

    item.set_command("")
    item.activate()
    assert fired == ["demo.refresh"]

    assert bar.remove_item(item) is True
    assert bar.items() == []
    assert bar.remove_item(item) is False
    bar.deleteLater()


def test_status_bar_palette_follows_theme(qapp: Any) -> None:
    palette.reset()
    bar = StatusBar()
    item = bar.add_item("状态", "left", 0, command="demo.refresh")
    palette.set_active({"SURFACE_MUTED": "#101010", "LINE": "#333333", "TEXT": "#eeeeee"})
    bar.apply_palette()
    assert "#101010" in bar.styleSheet()
    assert "#333333" in bar.styleSheet()
    label = item.findChild(QLabel)
    assert label is not None and "#eeeeee" in label.styleSheet()
    palette.reset()
    bar.deleteLater()


# ---------- 输出面板 ----------
def test_output_panel_channels_and_append(qapp: Any) -> None:
    palette.reset()
    panel = OutputPanel()
    assert panel.channels() == []
    assert panel.isHidden() is True
    panel.append_line("demo", "第一行")
    panel.append("demo", "追加")
    assert panel.channels() == ["demo"]
    assert panel.current_channel() == "demo"
    assert panel.text() == "第一行\n追加"

    panel.append_line("other", "其它")
    assert panel.channels() == ["demo", "other"]
    assert panel.current_channel() == "demo"
    assert panel.text() == "第一行\n追加"
    assert panel.text("other") == "其它\n"

    assert panel.show_channel("other") == "other"
    assert panel.isHidden() is False
    assert panel.current_channel() == "other"
    assert panel.text_widget().toPlainText() == "其它\n"

    panel.clear("other")
    assert panel.text("other") == ""
    assert panel.text_widget().toPlainText() == ""
    with pytest.raises(ValueError, match="通道名"):
        panel.create_channel("  ")
    panel.deleteLater()


def test_output_panel_palette_follows_theme(qapp: Any) -> None:
    palette.reset()
    panel = OutputPanel()
    palette.set_active({"SURFACE": "#0a0a0a", "TEXT": "#fafafa", "LINE": "#222222", "SURFACE_MUTED": "#111111"})
    panel.apply_palette()
    assert "#0a0a0a" in panel.styleSheet()
    header = panel.findChild(QFrame, "obox-output-header")
    assert header is not None and "#111111" in header.styleSheet()
    assert "#fafafa" in panel.text_widget().styleSheet()
    palette.reset()
    panel.deleteLater()