---
status: done
---

# 扩展 API 全面扩充 Spec Delta

## Purpose

把扩展 API 按 VS Code 命名空间重组并补全：window/workspace/commands/env/extensions + storage/network/message/log，函数与参数用 camelCase；window 增加模态框与新窗口，network 增加多协议与统一代理。

## ADDED Requirements

### Requirement: 命名空间与命名

扩展 API SHALL 按命名空间组织：window、workspace、commands、env、extensions、storage、network、message、log。函数名与参数名 SHALL 使用 camelCase，并尽量沿用 VS Code 同名语义；扩展 SHALL 只通过 obox.api 使用能力，不直接 import Qt。

#### Scenario: 扩展调用命名空间 API
- **WHEN** 扩展导入 window.showInformationMessage 与 commands.executeCommand
- **THEN** 无需 Qt 依赖即可调用，参数名为 camelCase

### Requirement: window 消息与选择

window SHALL 提供 showInformationMessage、showWarningMessage、showErrorMessage（可带按钮项，返回选中项或 undefined）、showQuickPick、showInputBox、showOpenDialog、showSaveDialog；后两者复用文件选择器。

#### Scenario: 信息消息带按钮
- **WHEN** 调用 showInformationMessage("完成", "打开", "关闭")
- **THEN** 返回用户点击的按钮文本，取消返回 undefined

#### Scenario: 快速选择
- **WHEN** 调用 showQuickPick 并选中一项
- **THEN** 返回该项；取消返回 undefined

### Requirement: window 模态框

window SHALL 提供 showMessageBox(options)，支持 type、title、message、detail、buttons、defaultId、cancelId、checkboxLabel；对发起窗口模态，不阻塞其它窗口；返回 {response, checkboxChecked}。

#### Scenario: 模态只阻塞发起窗口
- **WHEN** 子窗口发起 showMessageBox
- **THEN** 子窗口不可交互，主窗口与其它子窗口仍可操作

### Requirement: window 新窗口

window SHALL 提供 createWindow(options)、closeWindow、setWindowTitle、getActiveWindow、listWindows、focusWindow。createWindow 支持 title、oml/html、width、height、parent、modal、singleton，返回 windowId；singleton 相同则复用已有窗口。

#### Scenario: 创建新窗口
- **WHEN** 扩展调用 createWindow({title, oml})
- **THEN** 新窗口打开并渲染 OML，返回 windowId

#### Scenario: 关闭与列举
- **WHEN** 调用 closeWindow(windowId) 与 listWindows()
- **THEN** 窗口关闭，列表不再包含该 id

### Requirement: window 状态栏与输出

window SHALL 提供 createStatusBarItem（text、tooltip、command、show/hide/dispose）、withProgress（title、cancellable、task）、createOutputChannel（append/appendLine/show/dispose 与 trace/debug/info/warn/error）、activeColorTheme 与 onDidChangeActiveColorTheme。状态栏项按 priority 排序。

#### Scenario: 进度与输出
- **WHEN** 调用 withProgress 并在 task 中 createOutputChannel 写日志
- **THEN** 主窗口显示进度，输出通道可查看日志

### Requirement: workspace

workspace SHALL 提供 workspaceFolders、getConfiguration(section)、findFiles(include, exclude, maxResults)、createFileSystemWatcher(glob)、fs.readFile(uri)、onDidChangeConfiguration。findFiles 只读且结果上限 2000；getConfiguration 返回 get/has/update。

#### Scenario: 读取工作区配置
- **WHEN** 调用 getConfiguration("obox").get("theme")
- **THEN** 返回当前配置值或 defaultValue

### Requirement: commands

commands SHALL 提供 registerCommand(commandId, callback)、executeCommand(commandId, ...args)、getCommands()；executeCommand 等待回调返回值并支持参数。

#### Scenario: 执行命令并取返回值
- **WHEN** 扩展注册命令并在另一处 executeCommand 调用
- **THEN** 返回该命令回调的结果

### Requirement: env

env SHALL 提供 appName、appVersion、language、appHost、platform、arch、clipboard.readText/writeText、openExternal(uri)、openPath(path)。

#### Scenario: 读写剪贴板
- **WHEN** 调用 env.clipboard.writeText("x") 后 readText()
- **THEN** 返回 "x"

### Requirement: extensions

extensions SHALL 提供 all、getExtension(id)、onDidChange；扩展描述包含 id、name、version、directory、storagePath、status、origin。

#### Scenario: 获取当前扩展目录
- **WHEN** 扩展调用 extensions.getExtension(context.extensionId)
- **THEN** 返回包含 directory 与 storagePath 的对象

### Requirement: storage

storage SHALL 提供 globalState 与 workspaceState，各含 get(key, defaultValue)、update(key, value)、keys()；数据落扩展 storage 目录，global 与 workspace 分开。

#### Scenario: 状态持久化
- **WHEN** globalState.update("count", 1) 后重启扩展
- **THEN** globalState.get("count") 返回 1

### Requirement: network 请求

network SHALL 提供 request(options)，options 含 method、url、headers、body、timeout、noProxy；返回 {status, headers, body}；HTTPS 证书校验由 sslStrict 控制。

#### Scenario: GET 请求
- **WHEN** 调用 request({url}) 且服务端 200
- **THEN** 返回 status=200 与响应体

### Requirement: network 多协议

network SHALL 提供 tcpConnect、udpSend、quicRequest、sshConnect、sftpList、ping。TCP/SSH/SFTP 支持 SOCKS5 或 HTTP CONNECT；UDP/QUIC 支持 SOCKS5 UDP associate（服务端支持时）；ICMP 仅直连，代理启用且未 noProxy 时返回明确错误。QUIC 使用 aioquic。

#### Scenario: SSH 走代理
- **WHEN** 设置启用 SOCKS5 代理并调用 sshConnect
- **THEN** 通过代理建立 SSH 会话

#### Scenario: ICMP 不支持代理
- **WHEN** 代理启用且 ping 未设置 noProxy
- **THEN** 返回「ICMP 不支持代理」错误

### Requirement: 网络代理设置

设置页 SHALL 新增「网络」分类：enabled、proxyUrl、sslStrict、noProxy（每行一个）。network 调用 SHALL 自动读取；调用参数只保留 noProxy 布尔值用于本次直连。

#### Scenario: 默认走代理
- **WHEN** 设置启用代理且 network.request 未传 noProxy
- **THEN** 请求经代理发出

### Requirement: message

message SHALL 提供 send(target, messageId, payload)、request(target, messageId, payload, timeout)、broadcast、on(messageId, listener)；target 可为 obox 或扩展 id。

#### Scenario: 请求应答
- **WHEN** 扩展 request("obox", ...) 且宿主应答
- **THEN** 返回 payload

### Requirement: log

log SHALL 提供 createOutputChannel(name)，通道含 append、appendLine、show、dispose、trace/debug/info/warn/error；日志落扩展 storage 目录。

#### Scenario: 输出日志
- **WHEN** 调用 channel.info("started")
- **THEN** 输出面板出现该行，文件同步写入

## MODIFIED Requirements

### Requirement: 注册点

改自基线「注册点」：命令除注册外 SHALL 支持执行与列举，命令回调可接收参数并返回结果。

#### Scenario: 命令可执行
- **WHEN** 扩展注册命令后调用 executeCommand
- **THEN** 回调被调用并返回结果

### Requirement: 设置扩展

改自基线「设置扩展」：设置分类 SHALL 增加「网络」，含代理启用、地址、sslStrict、忽略地址；写入 config.json 并广播变更。

#### Scenario: 网络设置生效
- **WHEN** 在设置页填写代理地址并启用
- **THEN** config.json 保存该代理，network API 自动使用

## Impact

- 新增 9 个命名空间的 API 与消息；window 增加模态与新窗口
- 设置页新增网络分类；网络依赖 aioquic（新增）
- 技能与文档按命名空间重写
- 既有 picker/app/view 能力保留并归位引用