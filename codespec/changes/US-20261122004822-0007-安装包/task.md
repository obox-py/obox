---
status: done
---

# Tasks

| ID | 任务 | 方式 | 涉及文件 | 需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 运行期路径解析 | 主 Agent | obox/runtime.py、obox/app.py | 运行期路径解析 | - | 安装态用 exe 目录与 LOCALAPPDATA；源码态不变 | 完成 |
| T2 | 三根扩展扫描 | 主 Agent | obox/extensions/{loader,host,supervisor}.py | 系统扩展扫描、扩展目录与清单 | T1 | 三个根都被扫描，优先级生效并有日志 | 待办 |
| T3 | exe 构建脚本 | 主 Agent | scripts/build_exe.py | 安装包构建 | T2 | build/obox.dist/obox.exe 生成 | 待办 |
| T4 | NSIS 脚本与安装器构建 | 主 Agent | installer/obox.nsi、scripts/build_installer.py | 安装包构建、安装目录布局 | T3 | dist/obox-{version}-setup.exe 生成 | 待办 |
| T5 | 安装与运行实测 | 主 Agent | dist、临时安装目录 | 安装目录布局、运行期路径解析 | T4 | 装到临时目录能启动；配置写到 LOCALAPPDATA | 待办 |
| T6 | 文档与技能同步 | 主 Agent | README.md、docs/arch.md、codespec/specs/、.agents/skills/obox-ext-dev | 全部 | T5 | 基线合并 check 0；技能更新 | 待办 |

## 任务详情

- T1：`uv run python -c "from obox.runtime import resolve; print(resolve())"`（源码态指向仓库根与 .obox）
- T2：`uv run pytest -q tests/test_loader_roots.py`（新增三根用例）
- T3：`uv run python scripts/build_exe.py` → build/obox.dist/obox.exe
- T4：`uv run python scripts/build_installer.py` → dist/obox-*-setup.exe
- T5：静默安装到临时目录后启动并检查 LOCALAPPDATA/obox/config.json
- T6：`check.py --baseline-only` 0；ruff/pytest 全绿

## 测试策略

路径解析与三根扫描走单测；exe 与安装包走一次真实构建；安装态用静默安装到临时目录验证。

## 自检

- [x] 需求都有任务覆盖
- [x] 任务有验收命令
- [x] 依赖无环

## 执行顺序

1. T1 → T2 → T3 → T4 → T5 → T6