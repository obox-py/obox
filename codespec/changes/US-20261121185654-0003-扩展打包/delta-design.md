---
status: done
---

# 扩展打包 Delta Design

## Context

扩展加载目前只有一条路径：扫描 extensions/ 下的目录，按 extension.json 校验后用 importlib 从 extension.py 加载。本轮增加打包（源码→pyd→.oix）与安装（.oix→.obox/extensions/{id}）两条路径，加载侧增加 pyd 分支与模块搜索路径注入。

## Scope

范围是打包脚本、安装解压、双目录扫描与 pyd 加载；不在范围：签名、在线分发、升级回滚。

## Changes

| 模块路径 | 改动 | 对齐的需求 | 结构影响 |
|---|---|---|---|
| scripts/pack_extension.py | 新增：解析本地 import 图，逐文件 Nuitka 编译，zip 打包到 dist | 扩展打包产物 | 新增构建入口 |
| obox/extensions/loader.py | 修改：扫描 .obox/extensions 与 extensions/，识别 .oix 并解压安装 | 扩展安装、扩展目录与清单 | 扫描面从单根变双根，多一步安装 |
| obox/extensions/manifest.py | 修改：入口允许 extension.py 或 extension.pyd | 扩展目录与清单 | 校验规则放宽 |
| obox/extensions/host.py | 修改：优先加载 extension.pyd，加载前把扩展目录加入 sys.path，并记录模块重名告警 | pyd 入口加载与模块搜索路径 | 宿主新增 pyd 加载分支 |
| tests/ | 新增：import 图分析、打包结构、安装与扫描、pyd 加载用例 | 全部 | 断言覆盖三条路径 |
| README.md | 修改：补打包命令、安装位置与加载顺序 | 全部 | 门面补使用方式 |

## Baseline Diff

| 基线文件 | 章节 | 变为什么 |
|---|---|---|
| codespec/specs/spec.md | Requirement: 扩展目录与清单 | 整节替换为「双根扫描 + 入口可为 pyd + .oix 先解压」 |
| codespec/specs/design.md | D11 模块布局 | 补一句：安装目录 .obox/extensions 与开发目录 extensions/ 并存 |
| docs/arch.md | 4.1、7.1 | 标注安装目录与打包产物 dist/ |
| README.md | 扩展开发、目录结构 | 补打包与安装说明 |

## Risks / Rollback

| 风险 | 触发条件 | 影响 | 应对 |
|---|---|---|---|
| 模块名跨扩展冲突 | 两个扩展都有 utils.py | 后加载者拿到别人的模块 | 记录告警；文档要求本地模块带前缀 |
| 编译耗时 | 每个 py 都起一次 Nuitka | 打包慢 | 只编入口可达的文件；先解析 import 图再编译 |
| pyd 与 Python 版本绑定 | 换 Python 版本 | 已装扩展无法加载 | 清单记录构建版本，加载失败给出明确提示 |
| 覆盖安装残留 | 新包文件更少 | 旧文件残留 | 覆盖前清空目标目录 |
| zip 路径穿越 | 恶意包内 ../ | 写到安装目录外 | 解压时校验成员路径必须落在目标目录内 |

回滚：删除 scripts/pack_extension.py，加载侧只保留 extension.py 分支，扫描退回 extensions/ 单根。
