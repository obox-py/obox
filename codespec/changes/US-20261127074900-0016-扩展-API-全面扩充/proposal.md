---
status: done
---

# 扩展 API 全面扩充 · VS Code 风格分类

## 背景

现有 obox.api 只有 app、view、settings、picker、component、i18n、lifecycle 等零散消息，缺少窗口、命令、通知、存储、工作区、环境、网络、扩展信息与统一消息入口。按 VS Code API 的命名空间、函数名与参数名整理，并补齐 window 的模态框与新窗口。

## 目标

- 命名空间对齐 VS Code：window、workspace、commands、env、extensions；自定义补充 storage、network、message、log
- 函数与参数一律 camelCase，沿用 VS Code 语义：showInformationMessage、showQuickPick、executeCommand、getConfiguration、createOutputChannel 等
- window 提供模态框与新窗口 API
- network 提供 http/tcp/udp/quic/ssh/sftp/icmp 与统一代理策略
- 所有 API 走消息 + Request 异步，不暴露 Qt
- 文档与 ext-dev 技能按命名空间重写

## 范围

**做：**

- 9 个命名空间：window、workspace、commands、env、extensions、storage、network、message、log
- window：showInformationMessage/showWarningMessage/showErrorMessage、showQuickPick、showInputBox、showOpenDialog/showSaveDialog、showMessageBox（模态）、createWindow、closeWindow、setWindowTitle、getActiveWindow、listWindows、focusWindow、createStatusBarItem、withProgress、createOutputChannel、activeColorTheme、onDidChangeActiveColorTheme
- workspace：workspaceFolders、getConfiguration、findFiles、createFileSystemWatcher、fs.readFile（只读）、onDidChangeConfiguration
- commands：registerCommand、executeCommand、getCommands
- env：appName、appVersion、language、appHost、platform、arch、clipboard.readText/writeText、openExternal、openPath
- extensions：all、getExtension、onDidChange
- storage：globalState/workspaceState（get/update/keys）
- network：request、tcpConnect、udpSend、quicRequest、sshConnect、sftpList、ping；设置代理自动生效，noProxy 按调用直连
- message：send、request、broadcast、on
- log：createOutputChannel（append/appendLine/show/dispose）、trace/debug/info/warn/error
- 设置页新增「网络」：启用代理、代理地址、sslStrict、忽略地址
- 文档、类型示例与 ext-dev 技能同步；示例扩展示范窗口、通知、网络

**不做：**

- 不做 terminal、webview、debug、tasks、scm、languages 等无对应 UI 的命名空间
- 不做任意文件写（workspace.fs 只读；扩展自己目录用 storage）
- 不改变扩展清单格式
- 不暴露 Qt 类型

## 需求草案

1. 命名空间对齐 VS Code，函数与参数一律 camelCase
2. window 提供消息框、quickPick、inputBox、打开/保存对话框、withProgress、createOutputChannel、statusBarItem
3. window.showMessageBox 对发起窗口模态；其余通知类非阻塞
4. window.createWindow 支持 title/oml/html/width/height/parent/modal/singleton，返回 windowId
5. window 支持 close/setTitle/getActive/list/focus
6. workspace 提供 workspaceFolders、getConfiguration、findFiles、createFileSystemWatcher、fs.readFile、onDidChangeConfiguration
7. commands 提供 registerCommand、executeCommand、getCommands
8. env 提供 appName/appVersion/language/appHost/platform/arch、clipboard、openExternal/openPath
9. extensions 提供 all/getExtension/onDidChange
10. storage 提供 globalState/workspaceState 的 get/update/keys
11. network 提供 request/tcpConnect/udpSend/quicRequest/sshConnect/sftpList/ping
12. 代理由设置页统一配置并自动生效，调用只保留 noProxy；sslStrict 可关
13. HTTP/HTTPS 支持；TCP/SSH/SFTP 走 SOCKS5/HTTP CONNECT；UDP/QUIC 走 SOCKS5 UDP associate；ICMP 仅直连
14. message 提供 send/request/broadcast/on
15. log 提供 createOutputChannel 与 trace/debug/info/warn/error
16. theme 信息放 window.activeColorTheme，并提供 onDidChangeActiveColorTheme
17. 文档与 ext-dev 技能按命名空间更新，附示例
18. 两套 Qt 绑定下测试与示例通过

## API 清单（草案）

### window
```text
showInformationMessage(message, ...items) -> string | undefined
showWarningMessage(message, ...items)
showErrorMessage(message, ...items)
showMessageBox(options) -> {response, checkboxChecked}   # 模态，对发起窗口
showQuickPick(items, options) -> item | undefined
showInputBox(options) -> string | undefined
showOpenDialog(options) -> uri[] | undefined
showSaveDialog(options) -> uri | undefined
createWindow(options) -> windowId
closeWindow(windowId)
setWindowTitle(windowId, title)
getActiveWindow() -> windowId | undefined
listWindows() -> windowId[]
focusWindow(windowId)
createStatusBarItem(alignment?, priority?) -> StatusBarItem
withProgress(options, task) -> Promise
createOutputChannel(name, options?) -> LogOutputChannel
activeColorTheme -> {kind, name, colors}
onDidChangeActiveColorTheme(listener)
```

### workspace
```text
workspaceFolders -> {uri, name, index}[]
getConfiguration(section?) -> {get(key, defaultValue), has(key), update(key, value, target?)}
findFiles(include, exclude?, maxResults?) -> uri[]
createFileSystemWatcher(glob) -> {onDidCreate, onDidChange, onDidDelete, dispose}
fs.readFile(uri) -> Uint8Array
onDidChangeConfiguration(listener)
```

### commands / env / extensions
```text
commands.registerCommand(commandId, callback, thisArg?)
commands.executeCommand(commandId, ...args) -> any
commands.getCommands(filterInternal?) -> string[]
env.appName / appVersion / language / appHost / platform / arch
env.clipboard.readText() / writeText(text)
env.openExternal(uri) / openPath(path)
extensions.all -> Extension[]
extensions.getExtension(id) -> Extension | undefined
extensions.onDidChange(listener)
```

### storage / network / message / log
```text
storage.globalState.get(key, defaultValue?) / update(key, value) / keys()
storage.workspaceState.get(key, defaultValue?) / update(key, value) / keys()
network.request(options) -> {status, headers, body}
network.tcpConnect(options) -> {connect, send, close, onData}
network.udpSend(options) -> {bytes}
network.quicRequest(options) -> {status, headers, body}
network.sshConnect(options) -> session
network.sftpList(options) -> entries[]
network.ping(host, options?) -> {alive, timeMs}
message.send(target, messageId, payload?)
message.request(target, messageId, payload?, timeout?) -> payload
message.broadcast(messageId, payload?)
message.on(messageId, listener) -> disposable
log.createOutputChannel(name) -> {append, appendLine, show, dispose, trace/debug/info/warn/error}
```

选项字段统一 camelCase：`placeHolder`、`canPickMany`、`ignoreFocusOut`、`password`、`value`、`prompt`、`validateInput`、`filters`、`defaultUri`、`saveLabel`、`openLabel`、`modal`、`parent`、`singleton`、`noProxy`、`sslStrict`。

## 网络与代理

- 代理来源只有设置页：启用开关、地址（http:// 或 socks5://）、sslStrict、忽略地址列表
- 调用不接收 proxy 参数；`noProxy: true` 强制本次直连
- HTTP/HTTPS 走 QtNetwork；TCP 走 SOCKS5/HTTP CONNECT；UDP 与 QUIC 走 SOCKS5 UDP associate；SSH/SFTP 复用 paramiko 并通过代理 socket；ICMP 仅直连，代理启用且未 noProxy 时返回明确错误
- QUIC 用 aioquic（新增依赖），保证 PyQt5/PySide6 一致
- sslStrict=false 时接受自签证书（https/quic），默认严格

## 关键取舍

- 命名空间与函数名对齐 VS Code，降低迁移成本；无 VS Code 对应的能力放自定义命名空间
- 模态框与新窗口只对发起窗口生效，不阻塞其它窗口
- storage 隔离到扩展 storage 目录，分 global/workspace
- workspace.fs 只读，避免越权写项目
- 网络统一由宿主代理，扩展不直接建 socket

## 与基线的冲突

- 基线无上述命名空间，需 ADDED 多组 Requirement
- 基线命令只有注册无执行/列举，需 MODIFIED
- 设置页需新增网络分类与配置项
- 技能与 README 的 API 索引按命名空间重写

## 假设

- 新窗口复用 AppWindow 与 OML 渲染
- 状态栏项放主窗口底部，按 priority 排序
- findFiles 限定工作区与扩展目录，上限 2000
- 保存对话框只返回路径，不写文件
- ICMP 走系统 ping，不要求管理员

## 验收判据

- 14 个命名空间/能力的 API 均有消息定义、文档与示例
- window 模态框只阻塞发起窗口；新窗口可创建/关闭/聚焦
- 两套 Qt 绑定下 pytest 与示例扩展可用
- 文档与技能按命名空间列出函数、参数与返回