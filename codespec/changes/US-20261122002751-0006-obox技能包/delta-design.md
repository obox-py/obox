---
status: done
---

# obox 技能包 Delta Design

## Context

工程已有 README、spec、design、arch 与 scripts/（verify_ui、ui_driver、build_theme、pack_extension）。本轮只新增 agent skill 文档与脚本，不改运行时。

## Scope

四个 agent 技能的 SKILL.md、references、templates 与 scripts；不含运行时改动。

## Changes

| 路径 | 改动 | 需求 |
|---|---|---|
| .agents/skills/obox-ext-dev/** | 新增 SKILL.md、references、templates、scripts | 扩展开发技能 |
| .agents/skills/obox-theme-dev/** | 新增 SKILL.md、references、templates、scripts | 主题开发技能 |
| .agents/skills/obox-ui-test/** | 新增 SKILL.md、references、templates、scripts | 界面验证技能 |
| .agents/skills/obox-test/** | 新增 SKILL.md、references、templates、scripts | 测试检查技能 |
| README.md | 新增「Agent 技能」一节 | 技能目录约定 |
| AGENTS.md | 新增组件与 API 变更同步技能的强制规则 | 组件与 API 变更同步技能 |

## 决策

- 按对象切分技能（扩展 / 主题 / 界面验证 / 测试），触发词互不重叠
- 脚本复用 scripts/ 与 obox 包（load_manifest、validate_component_class、verify_ui），不复制实现
- 校验脚本以退出码表达结果，便于 agent 直接判断

## Baseline Diff

| 基线文件 | 章节 | 变为什么 |
|---|---|---|
| codespec/specs/spec.md | 新增四条技能需求 + 目录约定 | 追加 |
| codespec/specs/design.md | D22 技能包 | 追加 |
| docs/arch.md | 目录与工具节 | 补 .agents/skills |
| README.md | 新增 Agent 技能 | 追加 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| 技能内容与代码漂移 | references 链到真实文件与命令，校验脚本随代码运行 |
| 四个技能内容重复 | 按对象切，模板与脚本各管一段 |
| 脚本依赖构建产物 | 校验脚本在缺少 .theme 时降级为源码校验并提示 |
