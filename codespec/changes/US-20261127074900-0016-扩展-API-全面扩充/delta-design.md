---
status: done
---

# 扩展 API 全面扩充 Design Delta

## Context

扩展运行在独立宿主进程，UI 与设置在主进程。API 需要两种落点：窗口/选择/状态栏等在 obox 主进程处理；网络、存储、扩展信息在宿主侧处理更自然，但要共享主进程的设置与 UI 状态。统一用 MessageBus + Request，扩展只看到 camelCase 函数。

## Scope

- 9 个命名空间的 API（ADDED）
- 命令执行与列举（MODIFIED 注册点）
- 设置页网络分类（MODIFIED 设置扩展）

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| obox/api/window.py | showInformation/Warning/Error、showQuickPick、showInputBox、showMessageBox、showOpenDialog/showSaveDialog、createWindow/close/setTitle/list/focus、statusBarItem、withProgress、outputChannel、activeColorTheme | window 全部 |
| obox/api/workspace.py | workspaceFolders、getConfiguration、findFiles、createFileSystemWatcher、fs.readFile、onDidChangeConfiguration | workspace |
| obox/api/commands.py | register/execute/getCommands | commands |
| obox/api/env.py | app 信息、clipboard、openExternal/openPath | env |
| obox/api/extensions.py | all/getExtension/onDidChange | extensions |
| obox/api/storage.py | globalState/workspaceState | storage |
| obox/api/network.py | request/tcpConnect/udpSend/quicRequest/sshConnect/sftpList/ping | network |
| obox/api/message.py | send/request/broadcast/on | message |
| obox/api/log.py | createOutputChannel/levels | log |
| obox/app.py | window/命令/状态栏/进度/输出/剪贴板/shell 的处理器；设置网络项 | window、env、commands、log |
| obox/extensions/host.py | network/storage/extensions/message 处理器 | 其余命名空间 |
| obox/extensions/context.py | 暴露 ctx.window/workspace/commands/... 便捷属性 | 全部 |
| obox/ui/statusbar.py、output_panel.py | 状态栏与输出面板 | window、log |
| extensions/settings | 网络设置页 | 设置扩展 |
| pyproject | aioquic | network |
| 测试/文档/技能 | 单测、verify、docs/api、ext-dev | 全部 |

## Decisions

- 命名空间与函数/参数完全对齐 VS Code；无对应能力的放 storage/network/message/log。
- 扩展侧不 import Qt；所有调用是消息，返回用 Request 等待；默认超时 30s，网络可传 timeout。
- window 类（消息框、quickPick、inputBox、打开/保存）发到 obox 主进程；showMessageBox 用 QDialog + WindowModal，父窗口由 message.src 映射到当前活动窗口。
- createWindow 复用 AppWindow：生成 window_id，OML 走 APP_UI_MSG，数据走 app.windowId；singleton 用 id 去重；modal 仅对 parent 生效。
- 状态栏项由主窗口维护，按 priority 排序；withProgress 用主窗口进度条，取消发回扩展。
- 输出通道在扩展 storage 落 .log 文件，同时在主窗口输出面板追加。
- workspace/extension/storage 由宿主处理：宿主已有 install/system/source/dev 根与扩展目录；storage 用 storageDir/extId/global|workspace.json。
- network 在宿主处理：HTTP 用 QtNetwork，TCP/UDP 用 QTcpSocket/QUdpSocket，SSH/SFTP 用 paramiko，ICMP 调系统 ping，QUIC 用 aioquic。代理设置由主进程在配置变化时推给宿主。
- 代理策略集中在 host/network/proxy.py：resolve(no_proxy) 返回 direct 或代理配置；不提供按调用传 proxy。
- commands 的 register 已在 context；新增 execute/get 走宿主 CommandRegistry，参数 JSON 序列化，返回结果。
- message 直接封装 MessageBus：send 到 obox 或扩展 id，request 用 correlation_id，broadcast 用广播标志，on 注册 handler。
- 设置网络项：settings 扩展新增分类与控件，写入 config.json；主进程读取并推送给宿主。

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 新增 9 命名空间与 15 条 Requirement；修改注册点与设置扩展 |
| design.md | 新增 D53 API 命名空间与落点、D54 窗口/模态、D55 网络与代理 |
| docs/arch.md | 逻辑架构补 api 命名空间、network 服务、状态栏/输出面板 |
| README.md | 扩展开发补 API 分类索引 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| aioquic 体积与兼容 | 仅 network 导入；失败返回明确错误；可退回 PySide6 HTTP/3 |
| QtNetwork 在 PyQt5/PySide6 差异 | 统一走 obox.qt；网络单测用本地 socket |
| 代理下 UDP/QUIC 服务端不支持 | 返回能力错误，不静默直连 |
| ICMP 需权限 | 用系统 ping，失败明确报错 |
| 模态窗口错配父窗口 | 由消息 src 映射活动窗口，测试覆盖 |
| 状态栏/输出面板阻塞 UI | 主进程异步，限流；日志批量写 |