---
status: done
---

# Tasks

## 拆分方式

按可验证增量：消息契约、滚动控制器、装配与路由、测试与文档；设置页改版已撤回，不再列入任务。

## 全局约束

- 组件标签仍是 21 个；sticky 是属性不是新组件
- 锚点只认视图根的直接子组件，多个 sticky 只取第一个
- 滚动时长与偏移由消息给，缺省 600ms / 64px
- 不改 builder/parser/registry/main_window 的现有接口
- 不引入第三方依赖

## 任务清单

| ID | 任务 | 方式 | 涉及文件 / 模块 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 锚点消息契约 | 主 Agent | obox/api/view.py、tests/test_anchor.py | 视图锚点与滚动 | - | 两条消息可构造、可解码，字段有测试 | 完成 |
| T2 | 滚动控制器 | 主 Agent | obox/ui/anchor.py、tests/test_anchor.py | 视图锚点与滚动 | T1 | 目标值、夹取、当前锚点（含到顶到底）测试全绿 | 完成 |
| T3 | 装配吸顶与路由 | 主 Agent | obox/app.py、tests/test_anchor.py | 视图锚点与滚动、视图文件格式 | T2 | sticky 抬出滚动区，滚动消息驱动动画并回推锚点 | 完成 |
| T4 | 技能文档同步 | 主 Agent | .agents/skills/obox-ext-dev/references/context-api.md | 视图锚点与滚动 | T3 | 文档写清 sticky 与两条消息，check_all 通过 | 完成 |
| T5 | 重编与全量验证 | 后台 | .theme、tests、scripts/verify_ui.py | 全部 | T4 | pytest 全绿、verify 两套 0 失败 | 完成 |

## 任务详情

### T1 锚点消息契约

- 步骤：api/view.py 增两条消息与构造、解码测试
- 验收命令：`uv run pytest -q tests/test_anchor.py -k message`（期望：通过）

### T2 滚动控制器

- 步骤：AnchorController 实现 sections / scroll_to / current_anchor；动画用 OutCubic
- 验收命令：`uv run pytest -q tests/test_anchor.py -k controller`（期望：通过）

### T3 装配吸顶与路由

- 步骤：_mount_view 定位 sticky 并抬出；挂控制器；订阅滚动消息并回推锚点
- 验收命令：`uv run pytest -q tests/test_anchor.py`（期望：通过）

### T4 技能文档同步

- 步骤：context-api.md 补 sticky、滚动消息与锚点事件
- 验收命令：`uv run python .agents/skills/obox-test/scripts/check_all.py`（期望：退出码 0）

### T5 重编与全量验证

- 步骤：重编两套主题，跑全量 pytest 与两套 verify
- 验收命令：`uv run python scripts/build_theme.py light dark && uv run pytest -q && uv run python scripts/verify_ui.py --theme light && uv run python scripts/verify_ui.py --theme dark`（期望：全绿）

## 测试策略

TDD：控制器用离屏窗口与固定尺寸章节，期望值按「章节 y - 偏移」计算；设置页已还原，沿用原有断言。

## 执行顺序

1. T1 ∥ T2
2. T3
3. T4
4. T5

## 覆盖检查

- 视图锚点与滚动：T1、T2、T3
- 视图文件格式：T3

## 自检（落盘前）

- [x] 每条需求都被至少一个任务覆盖
- [x] 每个任务都有可复制执行的验收命令
- [x] 依赖无环
- [x] 方式只取 主 Agent / subagent / 后台
- [x] 模板占位与注释已全部替换
