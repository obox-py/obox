# obox 扩展 API

扩展只用 `obox.api` 的命名空间；所有函数第一个参数是 `ctx: OboxContext`（标识扩展与窗口，字段只读）。函数名与参数 camelCase，对齐 VS Code。

## OboxContext

| 字段/方法 | 说明 |
|---|---|
| extensionId / extension | 当前扩展 id 与清单快照（name/version/publisher/directory/status/origin） |
| extensionUri / extensionPath | 扩展目录 |
| globalStorageUri / storageUri / logUri | 扩展存储与日志目录 |
| extensionMode / activationReason | production/development/test；startup/command/view/app/dev |
| windowId | App 窗口上下文；None 表示主窗口 |
| subscriptions | 只读订阅袋：add(disposable)，卸载时统一 dispose |
| globalState / workspaceState | Memento：get(key, default)、update(key, value)、keys() |
| asAbsolutePath(relative) | 相对扩展目录解析并拒绝越界 |

## window

`showInformationMessage(ctx, message, *items)`、`showWarningMessage`、`showErrorMessage`、`showMessageBox(ctx, options)`（模态，返回 response/checkboxChecked）、`showQuickPick(ctx, items, options)`、`showInputBox(ctx, options)`、`showOpenDialog`、`showSaveDialog`、`createWindow(ctx, options)`（title/oml/html/width/height/parent/modal/singleton）、`closeWindow`、`setWindowTitle`、`getActiveWindow`、`listWindows`、`focusWindow`、`createStatusBarItem`、`updateStatusBarItem`、`disposeStatusBarItem`、`withProgress`、`createOutputChannel`、`activeColorTheme`、`onDidChangeActiveColorTheme`。

## workspace

`workspaceFolders(ctx)`、`getConfiguration(ctx, section)`（get/has/update）、`findFiles(ctx, include, exclude, maxResults)`（只读，上限 2000）、`createFileSystemWatcher(ctx, glob)`、`readFile(ctx, uri)`（只读）、`onDidChangeConfiguration(ctx, listener)`。

## commands / env / extensions

- `commands.registerCommand(ctx, commandId, callback)`、`executeCommand(ctx, commandId, *args)`、`getCommands(ctx)`
- `env.appName/appVersion/language/appHost/platform/arch`；`clipboard.readText/writeText`；`openExternal(uri)`、`openPath(path)`
- `extensions.all(ctx)`、`getExtension(ctx, id)`、`onDidChange(ctx, listener)`

## storage / message / log

- `storage.globalState.get(ctx, key, default)` / `update(ctx, key, value)` / `keys(ctx)`；workspaceState 同
- `message.send(ctx, target, messageId, payload)` / `request(..., timeout)` / `broadcast(...)` / `on(ctx, messageId, listener)`
- `log.createOutputChannel(ctx, name)` → append/appendLine/show/dispose/trace/debug/info/warn/error

## network

`request(ctx, options)`、`tcpConnect`、`tcpSend`、`tcpClose`、`udpSend`、`quicRequest`、`sshConnect`、`sftpList`、`ping(ctx, host, options)`。

- 设置页「网络」：启用代理、proxyUrl、sslStrict、noProxy 列表；启用后默认走代理
- 每次调用只可传 `noProxy=True` 强制直连，不接受 proxy URL 参数
- HTTP/HTTPS 走 QtNetwork；TCP/SSH/SFTP 走 SOCKS5/HTTP CONNECT；UDP/QUIC 走 SOCKS5 UDP associate；ICMP 仅直连，代理下返回错误
- sslStrict=False 时接受自签证书（https/quic）

## ctx 绑定命名空间

ctx 直接暴露绑定好的命名空间，调用时不必再传 ctx：

```python
ctx.window.showInformationMessage("完成")
ctx.commands.executeCommand("demo.refresh")
ctx.storage.globalState.update("count", 1)
ctx.network.request({"url": "https://example.com"})
```

等价的显式写法是 `window.showInformationMessage(ctx, ...)`。

## 示例

```python
from obox.api import window, commands, storage

def activate(ctx):
    ctx.subscriptions.add(
        commands.registerCommand(ctx, "demo.hello", lambda: window.showInformationMessage(ctx, "hi"))
    )
    count = storage.globalState.get(ctx, "count", 0)
    storage.globalState.update(ctx, "count", count + 1)
```