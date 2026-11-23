---
status: done
---

# Tasks

| ID | 任务 | 方式 | 涉及文件 | 需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 扩展开发技能 | 主 Agent | .agents/skills/obox-ext-dev/** | 扩展开发技能 | - | scaffold 生成可激活扩展；check 能拒绝坏清单 | 完成 |
| T2 | 主题开发技能 | 主 Agent | .agents/skills/obox-theme-dev/** | 主题开发技能 | - | 契约校验通过；模板可编译 | 完成 |
| T3 | 界面验证技能 | 主 Agent | .agents/skills/obox-ui-test/** | 界面验证技能 | T1 | 脚本跑两套主题并汇总 | 完成 |
| T4 | 测试检查技能 | 主 Agent | .agents/skills/obox-test/** | 测试检查技能 | T2 | 汇总 ruff/pytest/基线 | 完成 |
| T6 | AGENTS.md 同步规则 | 主 Agent | AGENTS.md | 组件与接口变更同步技能 | T4 | 规则含映射表与提交前命令 | 完成 |
| T5 | 验证与文档合并 | 主 Agent | README.md、docs/arch.md、codespec/specs/ | 技能目录约定 | T3、T4 | 四个脚本实测；基线合并 check 0 | 完成 |

## 任务详情

- T1：`uv run python .agents/skills/obox-ext-dev/scripts/scaffold_extension.py demo2 obox` 后用 check 脚本校验
- T2：`uv run python .agents/skills/obox-theme-dev/scripts/check_theme.py` → 0
- T3：`uv run python .agents/skills/obox-ui-test/scripts/run_verify.py` → 两套主题结果汇总
- T4：`uv run python .agents/skills/obox-test/scripts/check_all.py` → 0
- T5：`check.py --baseline-only` → 0

## 测试策略

每个脚本实际执行一次，确认退出码与输出；技能目录结构用 glob 核对。

## 自检

- [x] 每条需求都有任务覆盖
- [x] 脚本都有可执行命令
- [x] 依赖无环

## 执行顺序

1. T1 → T2 → T3 → T4 → T5