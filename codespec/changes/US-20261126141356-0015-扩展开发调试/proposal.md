---
status: done
---

# 扩展开发调试 · 本地目录加载与 VS Code 断点

## 背景

现在开发扩展要么放进源码 extensions/，要么打包成 .oix 安装。需要一种「开发模式」：把任意开发目录挂到本机已安装的 obox 上直接加载，不写入安装目录、不当作已安装扩展；能用 debugpy 在 VS Code 里加断点调试；改文件后自动重载。

## 目标

- 启动参数 --dev-extension（可重复）加载开发目录；运行中可通过消息加入/移除
- 开发目录只挂到扩展宿主，不复制、不安装、不写 disabled，卸载后不残留
- --debug 时扩展宿主以 debugpy 监听端口启动；仓库提供 .vscode/launch.json（attach 与 launch 两种）
- 开发目录记住到配置，下次启动继续加载；文件保存自动重启宿主并重激活
- 开发扩展在扩展列表里标记为 dev，不提供安装/卸载按钮

## 范围

**做：**

- CLI：--dev-extension、--debug、--debug-port、--debug-wait
- 配置：config.json 增加 dev_extensions；启动时合并 CLI 与配置
- 宿主：--dev-dir 参数，扫描来源加 dev；入口优先源码 extension.py
- 消息：DEV_EXTENSION_ADD_MSG / DEV_EXTENSION_REMOVE_MSG（obox 内部与扩展管理可用）
- 监听开发目录变化，自动重启宿主；--debug 时仍可关闭
- debugpy 启动包装与 .vscode/launch.json（attach 到 5678、launch 带 --dev-extension 示例）
- 文档：README、ext-dev 技能「如何调试扩展」

**不做：**

- 不做调试器 UI（断点在 VS Code 里加）
- 不把开发扩展打进 .oix
- 不改变已安装扩展的扫描顺序
- 不做远程调试隧道

## 需求草案

1. obox 接收 --dev-extension PATH（多次），路径必须含合法 extension.json
2. 开发目录作为独立来源加载，等同源码扩展，但不进安装目录与 disabled 列表
3. 开发目录列表写入配置并在下次启动自动加载；移除命令从配置删掉
4. --debug 时扩展宿主通过 debugpy 监听 127.0.0.1:5678（可改端口），等待 attach
5. 仓库提供 .vscode/launch.json：attach 扩展宿主 + launch obox 并加载示例开发扩展
6. 开发目录内文件变化时自动重启宿主；其它扩展不受影响
7. 开发扩展在扩展列表中标记 dev，不能「卸载」，只能「停止调试」
8. 不影响已安装扩展、主题与 .oix 流程
9. 文档给出 VS Code 配置与操作步骤

## 关键取舍

- 用 debugpy + DAP attach：VS Code 原生断点体验；宿主是独立进程，attach 不影响 obox UI
- 开发目录由 supervisor 传给宿主，宿主按 dev 来源扫描：不改安装/卸载语义
- 自动重载默认开：保存即生效；--debug 时可加 --no-dev-reload 关闭，避免断点被重启打断
- launch.json 进仓库：attach 为主（已运行 obox），launch 为辅助（一键起 obox + 加载示例目录）

## 与基线的冲突

- 基线扩展扫描只有安装/系统/源码三个来源，需 MODIFIED 加 dev 来源
- 基线 CLI 没有开发参数，需补
- 基线无需 debugpy 依赖：debugpy 作为开发依赖（dev group），不进运行时安装包

## 假设

- debugpy 放 dev 依赖；发布包不带
- 默认端口 5678；--debug-wait 控制是否等 attach 再激活
- 开发扩展的窗口/视图与正式扩展一致，只是列表标记 dev
