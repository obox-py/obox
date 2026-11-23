---
status: done
---

# Tasks

## 拆分方式

按可验证增量：i18n 回退、语言项、调色板、组件迁移、契约与装配、主题瘦身、图表、验证与文档各自独立；共 10 个任务。

## 全局约束

- 组件实现只有一份：obox/ui/components；主题包不再含组件代码
- 组件自绘颜色只从 palette 取，不内置十六进制常量
- i18n 注册必须含 zh-CN；解析顺序精确 → 语言基码 → zh-CN
- 组件标签是 21 + chart；主题 QSS 继续用对象名选择器
- 不引入除 matplotlib 之外的新依赖

## 任务清单

| ID | 任务 | 方式 | 涉及文件 / 模块 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | i18n 区域回退与强制缺省 | 主 Agent | obox/i18n.py、tests/test_i18n_switch.py、tests/test_i18n.py | 区域语言与缺省回退、i18n 注册与占位替换 | - | zh-HK/zh-TW 回退 zh-CN、en-GB 回退 en-US、缺 zh-CN 被拒，测试全绿 | 完成 |
| T2 | 语言项全量地区 | 主 Agent | obox/app.py、tests/test_settings_filter.py | 设置扩展 | T1 | 设置语言项列出 Qt 地区、原生名显示、搜索可用 | 完成 |
| T3 | 调色板模块 | 主 Agent | obox/ui/palette.py、tests/test_palette.py | 主题色板与文字层级 | - | Palette 字段齐全、set_active/取值、未初始化回退亮色 | 完成 |
| T4 | 迁移 21 个组件 | 主 Agent | obox/ui/components/**、tests/test_components.py 等 | 组件契约不变、主题色板与文字层级 | T3 | 组件从 palette 取色，旧测试改宿主表后全绿 | 完成 |
| T5 | 组件表与 provider 契约 | 主 Agent | obox/ui/components/__init__.py、obox/ui/component_protocol.py、obox/ui/builder.py、obox/ui/kit.py、obox/app.py | 界面套件清单与加载、组件能力接口与消息处理分界 | T4 | REQUIRED_TAGS 校验宿主表；provider 只校验样式；装配用宿主表 | 完成 |
| T6 | 主题瘦身与构建 | 主 Agent | theme/{light,dark}/{theme,provider}.py、theme/_build/*.py | 界面套件清单与加载、主题色板与文字层级 | T4 | 主题无组件、导出 PALETTE；构建只打包样式 | 完成 |
| T7 | 图表组件 | 主 Agent | obox/ui/components/chart.py、tests/test_chart.py | 图表组件 | T5 | data/title 状态、QtAgg 画布、缩放平移悬停重置，测试覆盖 | 完成 |
| T8 | 验证场景与回归 | 主 Agent | scripts/verify_ui.py | 图表组件、区域语言 | T6,T7 | 图表截图与交互断言、语言切 zh-HK 回退断言，两套主题 0 失败 | 完成 |
| T9 | 技能文档同步 | subagent | .agents/skills/obox-theme-dev/**、obox-ext-dev/**、obox-ui-test/** | 全部 | T5 | 主题只写样式、组件表 21+1、语言示例更新，check_all 通过 | 完成 |
| T11 | 主题 QSS 外置 | 主 Agent | theme/{light,dark}/styles.qss、theme.py、provider.py、scripts/build_theme.py | 界面套件清单与加载 | T6 | QSS 在独立文件里、加载后无 token 残留、构建复制到 .theme | 完成 |
| T10 | 重编与全量验证 | 后台 | .theme、tests、scripts/verify_ui.py、pyproject.toml | 全部 | T8,T9 | matplotlib 入依赖；pyd 只含样式；pytest 全绿；verify 两套 0 失败 | 完成 |

## 任务详情

### T1 i18n 区域回退与强制缺省

- 步骤：
  1. I18nRegistry.resolve：精确 → 语言基码（zh-*、en-*）→ zh-CN
  2. register 校验 values 必须含 zh-CN，缺失抛 I18nError
  3. 测试覆盖 zh-HK、zh-TW、en-GB、未知语言、缺 zh-CN
- 验收命令：`uv run pytest -q tests/test_i18n.py tests/test_i18n_switch.py tests/test_i18n_document.py`（期望：通过）

### T2 语言项全量地区

- 步骤：
  1. app._settings_groups 的语言项改为 Qt 地区列表（原生名，重复补地区代码）
  2. 设置搜索仍能过滤；选择后切语言并持久化
- 验收命令：`uv run pytest -q tests/test_settings_filter.py tests/test_i18n_switch.py`（期望：通过）

### T3 调色板模块

- 步骤：Palette 结构、set_active/active、默认值；测试字段与回退
- 验收命令：`uv run pytest -q tests/test_palette.py`（期望：通过）

### T4 迁移 21 个组件

- 步骤：
  1. 把 theme/{light,dark}/components 合并为 obox/ui/components 单份实现
  2. 颜色、圆角、控件高度改从 palette() 取
  3. 更新测试的 provider/组件表引用
- 验收命令：`uv run pytest -q tests/test_components.py tests/test_card.py tests/test_choice.py tests/test_flex.py`（期望：通过）

### T5 组件表与 provider 契约

- 步骤：
  1. 宿主组件表 21 + chart；REQUIRED_TAGS 校验宿主表
  2. validate_provider 只校验样式能力（stylesheet、palette、font_dir、icon 色、spacing）
  3. app 装配用宿主表；kit 校验新字段
- 验收命令：`uv run pytest -q tests/test_component_protocol.py tests/test_kit_loader.py tests/test_builder.py`（期望：通过）

### T6 主题瘦身与构建

- 步骤：
  1. theme.py 导出 PALETTE 字典；provider 去组件、暴露 palette
  2. 构建脚本只打包样式、调色板与字体；删除组件目录
- 验收命令：`uv run python -c "from theme.light import create_ui_provider as f; p=f(); print(hasattr(p,'palette'), hasattr(p,'component_types'))"`（期望：True False）

### T7 图表组件

- 步骤：
  1. chart 组件：FigureCanvasQTAgg、data/title 状态、line/bar/scatter
  2. 滚轮缩放、拖动平移、悬停坐标、重置按钮
  3. 测试：数据渲染、类型切换、缺失 matplotlib 时的降级提示
- 验收命令：`uv run pytest -q tests/test_chart.py`（期望：通过）

### T8 验证场景与回归

- 步骤：
  1. verify 增图表页截图与缩放后重置断言
  2. 语言切 zh-HK 断言回退到 zh-CN
- 验收命令：`uv run python scripts/verify_ui.py --theme light` 与 `--theme dark`（期望：0 失败）

### T9 技能文档同步

- 步骤：theme-dev 改为样式包；ext-dev 补 chart 与语言；ui-test 补场景编号
- 验收命令：`uv run python .agents/skills/obox-test/scripts/check_all.py`（期望：退出码 0）

### T10 重编与全量验证

- 步骤：matplotlib 入依赖并安装；重编两套主题；全量 pytest 与 verify
- 验收命令：`uv sync && uv run python scripts/build_theme.py light dark && uv run pytest -q && uv run python scripts/verify_ui.py --theme light && uv run python scripts/verify_ui.py --theme dark`（期望：全绿）

## 测试策略

TDD：i18n 与 palette 先写失败测试；组件迁移以现有测试为回归基线，逐组件对照旧实现后再改颜色来源；chart 用离屏画布断言数据点数量与视图范围。

## 执行顺序

1. T1 ∥ T3
2. T2 ∥ T4
3. T5
4. T6 ∥ T7
5. T8 ∥ T9
6. T10

## 覆盖检查

- 图表组件：T7、T8
- 区域语言与缺省回退：T1、T2、T8
- 界面套件清单与加载：T5、T6
- 组件契约不变：T4、T5
- 组件能力接口与消息处理分界：T5
- 主题色板与文字层级：T3、T4、T6
- i18n 注册与占位替换：T1
- 设置扩展：T2

## 自检（落盘前）

- [x] 每条需求都被至少一个任务覆盖
- [x] 每个任务都有可复制执行的验收命令
- [x] 依赖无环，且同文件任务没有并行
- [x] 方式只取 主 Agent / subagent / 后台
- [x] 模板占位与注释已全部替换