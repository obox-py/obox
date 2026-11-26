---
status: done
---

# 扩展开发调试 Design Delta

## Context

开发扩展目前只能放源码目录或装 .oix，缺少不安装、可断点、可热重载的加载路径；宿主独立进程使 debugpy attach 成为自然选择。

## Scope

- 开发扩展加载（ADDED）
- 断点调试（ADDED）
- 热重载（ADDED）
- 扩展目录与清单（MODIFIED）

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| `obox/main.py`、`obox/app.py` | --dev-extension/--debug/--debug-port/--no-dev-reload 参数；启动前设置 | 加载、调试、热重载 |
| `obox/extensions/supervisor.py` | 传递 --dev-dir；debug 时用 debugpy 包装宿主命令 | 加载、调试 |
| `obox/extensions/host.py` | 解析 --dev-dir，scan_all 增加 dev 来源 | 加载 |
| `obox/extensions/loader.py` | 支持 dev 根扫描（origin=dev） | 扩展目录与清单 |
| `obox/api/extensions.py` | DEV_EXTENSION_ADD/REMOVE 消息 | 加载 |
| `obox/app.py` | 处理 dev 消息、写配置、watch 开发目录并重启宿主 | 加载、热重载 |
| `.vscode/launch.json` | attach 与 launch 配置 | 调试 |
| `pyproject.toml` | dev 依赖加 debugpy | 调试 |
| 测试与文档 | CLI、配置、扫描、host 参数、launch.json 校验 | 全部 |

## Decisions

- 开发目录由 supervisor 传给宿主，宿主按 dev 来源扫描；不写安装目录。
- debug 用 `python -m debugpy --listen 127.0.0.1:PORT --wait-for-client -m obox.extensions.host ...`；不 debug 时保持现有启动方式。
- 默认端口 5678；--debug-wait 控制是否等 attach（默认等待，便于断点命中首次激活）。
- 开发目录变化用 QFileSystemWatcher，合并 300ms 防抖后 restart 宿主。
- 配置键 dev_extensions 保存绝对路径；DEV_REMOVE 同时从配置删除。
- 已安装与 dev 同 id 时 dev 覆盖（仅本次会话），管理页显示 dev 标记。

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| debug 等待 attach 时宿主不激活 | 文档写明先 attach；--no-debug-wait 可跳过 |
| 热重载打断断点 | --no-dev-reload 关闭 |
| dev 覆盖安装语义混淆 | 仅在本次会话生效并在列表标 dev |

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 新增开发扩展加载、断点调试、热重载；扩展来源加 dev |
| design.md | 新增 D50 开发目录来源、D51 debugpy attach、D52 热重载 |
| docs/arch.md | 宿主启动与扫描来源补 dev 与 debug 包装 |
| README.md | 开发调试一节与 VS Code 配置 |