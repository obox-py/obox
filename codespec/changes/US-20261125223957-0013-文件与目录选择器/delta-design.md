---
status: done
---

# 文件与目录选择器 Design Delta

## Context

扩展界面通过消息与 obox 交互，现有 API 没有文件系统能力；App 窗口与主窗口都是独立顶层窗口。Win11 风格对话框需要自绘/组合控件，SSH 浏览需要阻塞式网络 I/O，不能跑在 UI 线程。

## Scope

- 文件与目录选择器（ADDED）
- SSH 远端浏览（ADDED）
- 依赖与安装包（MODIFIED）

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| `obox/api/picker.py`（新） | PICKER_OPEN / PICKER_RESULT 与构造器；参数校验（mode、extensions、multi、ssh） | 选择器、SSH |
| `obox/app.py` | 处理 PICKER_OPEN：定位发起窗口、创建对话框、按窗口模态、完成后回 PICKER_RESULT | 选择器、按窗口模态 |
| `obox/ui/picker.py`（新） | Win11 风格对话框：快速访问、面包屑、搜索、详细信息列表、文件/目录模式、多选 | 选择器 |
| `obox/ui/picker_remote.py`（新） | paramiko 客户端：连接、列目录、默认目录、指纹校验；QThread 工作者 | SSH |
| `pyproject.toml` | 增加 paramiko | 依赖与安装包 |
| `tests/test_picker.py`（新） | 过滤、排序、路径解析、结果组装、模态窗口选择、SSH 客户端假实现 | 选择器、SSH |
| `scripts/verify_ui.py` | 打开选择器并截图（本地） | 选择器 |
| `extensions/demo` 或新示例 | 提供一个按钮发起 PICKER_OPEN | 选择器 |
| `.agents/skills/obox-ext-dev` | 文档补 picker 消息与参数 | 选择器 |

## Decisions

- 消息式 API：扩展发 PICKER_OPEN（带 window_id 可选），obox 回 PICKER_RESULT；扩展用 context.request 异步等待，不新增同步函数。
- 按窗口模态：对话框父窗口为发起窗口并设 Qt.WindowModal；主窗口发起阻塞主窗口，App 窗口发起只阻塞该窗口。
- 本地与远端统一为 Browser 抽象：list(path)、home()、join()；本地用 pathlib，远端用 paramiko SFTP；列表请求都走 QThread，结果用信号回 UI。
- 过滤：文件模式显示目录 + 匹配扩展名的文件；目录模式只显示目录；搜索在当前列表上按名称子串过滤。
- 结果：本地返回绝对路径字符串；远端返回 {path, host, user} 对象，paths 同时给字符串形式便于扩展直接展示。
- SSH 参数一次性传入（host/port/user/password/key_path/passphrase）；不持久化；认证失败在对话框内可重试。
- 指纹：首次连接用 paramiko 的缺失主机键回调，弹出确认框展示指纹，接受后仅本次会话记忆。
- paramiko 为必装依赖，安装包随 PyInstaller/Nuitka 正常带上。

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 新增「文件与目录选择器」「SSH 远端浏览」，依赖一节补 paramiko |
| design.md | 新增 D46 消息式选择器与按窗口模态、D47 paramiko 远端浏览与后台线程 |
| docs/arch.md | 逻辑架构补 obox/ui/picker 与 picker_remote 模块，部署架构补 paramiko 依赖 |
| README.md | 能力清单补文件选择器与 SSH 浏览 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| 大目录列表卡顿 | 列表虚拟化 + 限制 5000 项并提示 |
| SSH 网络超时 | connect/auth 超时 10s，错误显示在对话框 |
| 按窗口模态失效 | 单测断言 dialog.windowModality 与 parent |
| 依赖体积 | paramiko 约 10MB，可接受；失败则回退系统 sftp |

回滚：删除消息与对话框，不动现有组件。