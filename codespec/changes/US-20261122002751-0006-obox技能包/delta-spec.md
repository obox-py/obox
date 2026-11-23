---
status: done
---

# obox 技能包 Delta Spec

## ADDED Requirements

### Requirement: 扩展开发技能

工程 SHALL 提供 `.agents/skills/obox-ext-dev`：SKILL.md 说明何时使用与操作步骤；references 覆盖清单字段（views 只允许 sidebar/bottom、app、configuration）、context API、oml 指令与绑定、i18n.json、打包；templates 提供可直接拷贝的清单/入口/oml/i18n/图标；scripts 提供可运行的扩展脚手架与校验脚本。

#### Scenario: 脚手架生成可运行扩展
- **WHEN** 在仓库根执行 skill 的 scaffold 脚本并给出名称与作者
- **THEN** 生成的目录包含 extension.json、extension.py、views/main.oml、i18n.json、assets 图标，且 obox 能激活它

#### Scenario: 校验脚本发现坏清单
- **WHEN** 对缺字段或容器写 main 的目录运行校验
- **THEN** 脚本以非零退出并指出问题

### Requirement: 主题开发技能

工程 SHALL 提供 `.agents/skills/obox-theme-dev`：references 说明 21 个标签的组件契约、状态与事件、主题常量与 QSS、构建与切换 pyd；templates 提供组件与 theme.py 骨架；scripts 提供契约校验脚本与新增组件脚手架说明。

#### Scenario: 契约校验
- **WHEN** 对 theme/light 与 theme/dark 运行校验
- **THEN** 输出标签数、缺失标签与不合规组件，并通过时以 0 退出

### Requirement: 界面验证技能

工程 SHALL 提供 `.agents/skills/obox-ui-test`：references 覆盖 ui_driver 能力、verify_ui 的场景与截图、常见坑；templates 提供自定义场景片段；scripts 提供一键跑 light/dark 验证并汇总截图与退出码的脚本。

#### Scenario: 一键验证
- **WHEN** 运行 skill 的验证脚本
- **THEN** 依次跑两套主题，打印每组截图与退出码，任一失败则整体非零

### Requirement: 测试检查技能

工程 SHALL 提供 `.agents/skills/obox-test`：references 覆盖单测/e2e/pyd 集成矩阵、质量门禁与排障；templates 提供基于 fake_provider 的组件测试骨架；scripts 提供汇总 ruff、pytest、check.py 基线校验的脚本。

#### Scenario: 汇总检查
- **WHEN** 运行 skill 的检查脚本
- **THEN** 依次执行静态检查、测试与基线校验，汇总结果并以非零退出表示失败

### Requirement: 组件与接口变更同步技能

AGENTS.md SHALL 规定：任何组件标签/状态/事件/契约、theme 常量与 QSS、清单字段、context API、oml 指令、i18n.json、应用/配置贡献、打包产物、verify 场景或测试门禁发生变化时，必须在同一次改动中更新 .agents/skills 对应技能；提交前运行 check_all.py。

#### Scenario: 组件变化同步主题技能
- **WHEN** 新增或修改组件标签与契约
- **THEN** obox-theme-dev 的 references 与模板同步更新，标签计数保持一致

#### Scenario: 提交前检查
- **WHEN** 改完组件或 API
- **THEN** 运行 check_all.py 通过，技能与代码在同一提交里

### Requirement: 技能目录约定

四个技能 SHALL 遵循统一结构：SKILL.md 带 name 与 description frontmatter；references/templates/scripts 按需存在；脚本用 uv 在仓库根可直接运行；references 链接到仓库内真实文件与命令。

#### Scenario: 目录可被发现
- **WHEN** 列出 .agents/skills
- **THEN** 出现四个技能目录，各自 SKILL.md 的 name 与目录名一致