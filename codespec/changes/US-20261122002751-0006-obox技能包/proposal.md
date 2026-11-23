---
status: done
---

# obox 技能包 Proposal

## 背景

工程已经形成稳定的扩展/主题/验证/测试四类工作流，但知识散在 README、spec、design 与脚本里。需要把可复用的操作沉淀成四个 agent skill，放进 `.agents/skills`，每个都带 references、templates、scripts（没有的目录可以缺失）。

## 目标

- obox-ext-dev：按现有清单与 context API 写扩展，含 oml 视图、i18n.json、应用注册与打包
- obox-theme-dev：按 21 个标签的组件契约写主题套件与组件，并能构建/切换 pyd
- obox-ui-test：用 ui_driver 与 verify_ui 跑界面验证、截图与断言
- obox-test：单测、静态检查、文档校验与 e2e 的运行与排障

## 范围

**做**：四个 skill 的 SKILL.md；每个的 references/templates/scripts；可运行的脚手架与校验脚本。

**不做**：不新增运行时能力；不替代 codespec 流程；不写与本工程无关的通用技能。

## 需求草案

- 每个 skill 有 frontmatter（name/description）与「何时用/怎么做/边界」三段
- 内容以当前代码为准：容器只有 sidebar/bottom、21 个组件标签、contributes.app/configuration、i18n.json、.oix 打包
- scripts 至少一个可直接执行：脚手架或校验
- references 引用具体文件与命令，不写空泛建议
- templates 是能直接拷走改的文件

## 关键取舍

- 按对象切（扩展 / 主题 / 界面验证 / 测试），不按阶段切，避免四份内容互相重复
- 脚本复用现有 `scripts/` 与 `obox` 模块，不复制实现
- skill 只描述现状与操作步骤，规范仍以 codespec 为准（skill 里链回去）

## 与基线的冲突

- 基线没写过 agent skill；需要新增一节说明 `.agents/skills` 的四个技能与用途

## 假设

- 四个 skill 的触发词不交叉：扩展开发、主题/组件开发、界面验收、测试与检查
- 运行环境是仓库根目录，uv 可用
