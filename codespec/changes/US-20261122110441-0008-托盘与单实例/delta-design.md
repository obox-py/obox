---
status: done
---

# 托盘与单实例 Delta Design

## Context

当前关闭按钮直接退出进程，没有托盘，也没有实例互斥；设置页只有外观/语言/扩展/关于四类内置项。

## Scope

单实例管道、托盘对象、关闭询问对话框、设置新增行为分类与 close_action 配置；不涉及扩展 API 变更。

## Changes

| 模块 | 改动 |
|---|---|
| obox/ui/single_instance.py | 新增：按用户命名管道的探测与监听，第二实例发送显示请求 |
| obox/ui/tray.py | 新增：QSystemTrayIcon、菜单与双击恢复 |
| obox/ui/close_dialog.py | 新增：主题化三选一对话框 + 记住勾选 |
| obox/ui/main_window.py | closeEvent 改发信号，不再直接退出 |
| obox/app.py | 启动前单实例判定；托盘创建；关闭决策；设置项 close_action |
| tests/ | 新增关闭决策、单实例、设置映射用例 |

## Decisions

- 单实例用 QLocalServer/QLocalSocket，管道名含用户标识的短哈希，避免跨用户冲突；第二实例发送 show 后退出 0
- 关闭决策抽成纯函数 decide_close(action, choice, remember) 返回动作，便于单测
- 询问用自绘 QDialog（主题常量、38px 按钮、圆角 10），不用 QMessageBox
- close_action 存 settings.obox.close_action，枚举 ask/tray/quit，默认 ask；设置页「行为」分类第一项
- 托盘图标复用 assets/obox.svg；托盘菜单三项：显示主窗口、设置、退出

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 新增四条需求 |
| design.md | D24 托盘与关闭行为 |
| arch.md | 新增单实例/托盘模块 |
| README.md | 使用说明补托盘与关闭行为 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| 管道残留导致误判已运行 | 监听前先尝试连接；连不上则删除旧管道再监听 |
| 托盘不可用（远程/无桌面） | 托盘创建失败时退化为直接退出，不阻塞启动 |
| 隐藏到托盘后无法退出 | 托盘菜单与关闭对话框都提供退出 |
| 对话框阻塞自动化测试 | 决策逻辑抽纯函数，UI 只做展示 |
