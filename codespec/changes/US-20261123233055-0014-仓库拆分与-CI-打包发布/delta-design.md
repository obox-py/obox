---
status: done
---

# 仓库拆分与 CI 打包发布 Design Delta

## Context

主仓当前从 `.theme` 与 `extensions/` 读主题和扩展，构建脚本只产出本机安装包，没有远端与 CI。运行期已经支持系统扩展与用户扩展两处扫描（app 与 supervisor 都查 data_dir/extensions），主题仍只扫一个目录。

## Scope

- 仓库与发布流程（ADDED）
- 运行时资源目录（ADDED）
- 界面套件清单与加载、构建与 pyd 产物、扩展目录与清单（MODIFIED）

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| `obox/runtime.py` | 主题目录改为「安装目录 themes/ 或 .theme + 数据目录 themes/」；提供两处路径 | 运行时资源目录 |
| `obox/ui/kit.py` | 新增多目录扫描与去重（用户目录优先） | 界面套件清单与加载 |
| `obox/app.py` | 用合并后的主题列表；托盘与设置页同源 | 运行时资源目录 |
| `obox/extensions/host.py` | 安装 oix 时按进程架构选包（x64/arm64 后缀） | 扩展目录与清单 |
| `scripts/build_theme.py` | 产物目录可指定，支持 themes/<name> 布局 | 构建与 pyd 产物 |
| `scripts/build_exe.py` | 把 themes/ 与 extensions/ 编译目录放进 standalone | 构建与 pyd 产物 |
| `scripts/build_installer.py` | 安装包带 themes/ 与 extensions/，产物名带架构 | 构建与 pyd 产物 |
| `.github/workflows/build.yml`（主仓） | PR 测试 + tag 构建 x64/arm64 安装包并上传 Release | 仓库与发布流程、构建与 pyd 产物 |
| `extensions/rdp` → 独立仓 | 复制源码、打包脚本、workflow（双架构 oix） | 仓库与发布流程 |
| `extensions/webapp` → 独立仓 | 同上 | 仓库与发布流程 |
| 文档 | README 安装与 CI 说明、技能同步 | 全部 |

## Decisions

- 主题双源：安装目录优先取 `themes/`，源码态回退 `.theme`；数据目录 `themes/` 覆盖同名。
- 系统扩展随安装包编译成 `extensions 下按扩展标识命名的目录` 目录，宿主加载时与数据目录扩展合并，用户目录优先。
- oix 按架构命名 `扩展名-版本-win-x64.oix` / `-win-arm64.oix`，安装时由宿主的平台与架构决定选哪个；扩展管理选中一个包时按文件名后缀校验架构。
- 构建矩阵：windows-latest（x64）与 windows-11-arm（arm64）；ARM 用 PySide6 6.12 的 win_arm64 轮子。
- 发布：tag v* 触发；PR 只跑测试与打包冒烟。
- 仓库拆分：obox 仓保留主程序、系统扩展（app/settings/management）、主题源码；rdp 与 webapp 各自成仓，仅含自己目录、打包脚本与 workflow。

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| ARM runner 不可用 | arm64 任务标为 allowed-to-fail，Release 只发 x64 并注明 |
| 双源同名冲突 | 用户目录优先并有测试 |
| 安装包漏带 themes/extensions | 构建脚本产物断言 |

回滚：主题单源与本地发布脚本保留，删 CI 与架构判定即可。

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 按 delta-spec.md 的 2 条 ADDED 与 3 条 MODIFIED 合并 |
| design.md | 新增 D44「双源资源目录」、D45「按架构分发与安装」；构建一节补矩阵 |
| docs/arch.md | 目录结构图与构建流程补 themes/extensions 双源与两架构 |
| README.md | 安装、仓库与 CI 用法 |