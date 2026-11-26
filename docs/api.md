# obox 扩展 API

扩展只通过 `obox.api` 下的模块与宿主交互；每个模块都是一个消息类型或一组消息构造函数。扩展不要直接 import PySide6/PyQt5——obox 在两种绑定下都提供相同的 obox.api；确需 Qt 类型时用 `obox.qt`。

| 模块 | 能力 |
|---|---|
| `obox.api.component` | 组件事件、状态查询与状态修改（ComponentEventMessage / ComponentStateMessage / ComponentModifyMessage） |
| `obox.api.picker` | 文件与目录选择（PICKER_OPEN / PICKER_RESULT） |
| `obox.api.app` | 应用开窗、App 页面与数据注入（APP_OPEN_MSG / APP_UI_MSG / APP_VIEW_DATA_MSG） |
| `obox.api.view` | 视图数据、锚点滚动与吸顶（VIEW_DATA_MSG / VIEW_SCROLL_MSG / ANCHOR_CHANGED_MSG） |
| `obox.api.settings` | 设置列表与写入、扩展配置下发（SETTINGS_LIST_MSG / SETTINGS_SET_MSG / EXTENSION_CONFIG_MSG） |
| `obox.api.lifecycle` | 视图挂载完成等生命周期消息 |
| `obox.api.i18n` | i18n 注册消息 |
| `obox.api.message` | 消息基类、广播与请求应答 |

## 文件与目录选择

```python
from obox.api.picker import picker_open_message

request = context.request(
    picker_open_message(
        context.extension_id,
        mode="file",              # file 或 dir
        extensions=["txt", "md"], # 空列表 = 不过滤
        multi=False,
        title="选择文件",
        start_path="",
        window_id="",             # App 窗口传入自己的 window_id
        ssh=None,                 # {"host","port","user","password","key_path","passphrase"}
    ),
    timeout=3600,                 # 选择器可能长时间停留
)
payload = request.result()        # {"paths": [...], "cancelled": bool, "error": str}
```

- 模态范围由 `window_id` 决定：空值阻塞主窗口，App 窗口只阻塞该窗口。
- 本地结果返回绝对路径；远端结果返回 `{"path","host","user"}`。
- SSH 使用 paramiko，主机指纹自动记录、不弹确认；凭据只用于本次请求。
- 隐藏文件默认显示，可用「显示隐藏文件」开关收起；过滤与搜索对隐藏文件同样生效。
- 列表首行 `..` 返回上级；路径栏支持手输与最近路径下拉。
- SSH 主机键自动写入 `~/.ssh/known_hosts`；远端可「上传…」「下载…」（本地文件对话框），不支持远端新建文件夹。

## 示例

`extensions/pickerdemo` 提供本地/远端 × 文件/目录四个入口，可直接在侧栏「选择器示例」里试。完整调用约定见 `.agents/skills/obox-ext-dev/references/context-api.md`。

## 开发调试

- `--dev-extension PATH`：加载开发目录（可重复），不安装、不复制
- `--debug` / `--debug-port` / `--no-debug-wait`：宿主用 debugpy 监听，VS Code attach
- `--no-dev-reload`：关闭开发目录自动重载

消息（obox 内部与工具可用）：

| 消息 | payload | 作用 |
|---|---|---|
| `DEV_EXTENSION_ADD_MSG` | `{path}` | 挂载开发目录并写配置 |
| `DEV_EXTENSION_REMOVE_MSG` | `{path}` | 移除开发目录并重启宿主 |

详见 `.agents/skills/obox-ext-dev/references/debugging.md`。
