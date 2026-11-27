---
status: done
---

# Tasks

## 任务清单

| ID | 任务 | 方式 | 涉及文件 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 命名空间骨架与 ctx | 主 Agent | obox/api/*.py、context.py | 命名空间与命名 | - | 9 个模块可 import，ctx frozen | 完成 |
| T2 | window 消息与对话框 | 主 Agent | api/window.py、app.py、ui/picker.py | window 消息与选择 | T1 | showInformation/QuickPick/InputBox/Open/Save 可用 | 完成 |
| T3 | window 模态框 | 主 Agent | api/window.py、app.py、ui/modal.py | window 模态框 | T2 | 只阻塞发起窗口，返回 response | 完成 |
| T4 | window 新窗口 | 主 Agent | api/window.py、app.py、ui/app_window.py | window 新窗口 | T2 | create/close/setTitle/list/focus 可用 | 完成 |
| T5 | 状态栏/进度/输出/主题 | 主 Agent | ui/statusbar.py、output_panel.py、app.py | window 状态栏与输出 | T4 | 状态栏、进度、通道、主题事件可用 | 完成 |
| T6 | workspace | 主 Agent | api/workspace.py、host.py | workspace | T1 | folders/config/findFiles/watcher/readFile 可用 | 完成 |
| T7 | commands/env/extensions | 主 Agent | api/{commands,env,extensions}.py、host.py、app.py | commands、env、extensions、注册点 | T1 | 注册/执行/列举、env 信息、扩展列表 | 完成 |
| T8 | storage/message/log | 主 Agent | api/{storage,message,log}.py、host.py | storage、message、log | T1 | 持久化、请求应答、输出通道 | 完成 |
| T9 | network HTTP/TCP/UDP | 主 Agent | api/network.py、host/network/*.py | network 请求、多协议 | T1 | request/tcp/udp 可用，代理生效 | 完成 |
| T10 | network SSH/SFTP/ICMP/QUIC | 主 Agent | host/network/{ssh,icmp,quic}.py | network 多协议 | T9 | ssh/sftp/ping/quic 可用或明确报错 | 完成 |
| T11 | 设置页网络分类 | 主 Agent | extensions/settings/**、api/settings.py | 网络代理设置、设置扩展 | T9 | 四项配置落 config，API 自动读取 | 完成 |
| T12 | 文档、技能与测试 | 主 Agent | docs/api.md、ext-dev、tests | 文档与技能 | T2-T11 | 两绑定 pytest 通过，文档有分类索引 | 完成 |

## 任务详情

### T1 命名空间骨架与 ctx
- 步骤：建 9 个 api 模块，定义消息 id/构造函数；OboxContext 改 frozen + SubscriptionBag
- 验收：`uv run python -c "from obox.api import window, workspace, commands"`

### T2-T5 window
- 步骤：消息路由到 app；消息框/quickPick/inputBox/打开保存；createWindow 复用 AppWindow；状态栏/输出面板；主题事件
- 验收：示例扩展调用窗口与模态；verify 截图

### T6-T8 workspace/commands/env/extensions/storage/message/log
- 步骤：宿主侧处理器；配置与文件夹；命令执行；状态 JSON；消息总线封装；输出通道落盘
- 验收：单测覆盖 get/update、executeCommand、request

### T9-T10 network
- 步骤：proxy 解析；QtNetwork HTTP/TCP/UDP；paramiko SSH/SFTP；系统 ping；aioquic QUIC
- 验收：本地 HTTP 服务、TCP echo、SSH 真机、ICMP 直连；代理下错误明确

### T11-T12 设置与文档
- 步骤：settings 扩展网络分类；docs/api.md 按命名空间；ext-dev 模板与示例
- 验收：`check_all.py`、verify light/dark、两绑定 pytest

## 测试策略

TDD：每个 API 先写消息构造与 handler 单测；网络用本地 socket/HTTP server；UI 用离屏与 verify；真机 SSH/ICMP 单独记录。

## 执行顺序

T1 → T2 → T3/T4 ∥ T6-T8 → T5 → T9 → T10 → T11 → T12

## 自检

- [x] 每条需求都有任务覆盖
- [x] 验收命令可执行
- [x] 依赖无环
- [x] 方式只用 主 Agent / subagent / 后台