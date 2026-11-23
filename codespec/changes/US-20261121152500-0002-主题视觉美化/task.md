---
status: done
---

# Tasks

## 拆分方式

按可验证增量：每个任务都能用现有测试文件单独验收（test_card.py、test_components.py、test_settings_close.py、test_titlebar.py），回滚粒度细；最后 T14 统一重编 pyd 并跑全量验证。

## 全局约束

- 组件标签仍是 21 个，modal 标签名与状态名 visible / text 不变，不为浮层新增标签
- 两套套件保持镜像，theme/* 仍只依赖 PySide6，不 import obox
- 旧写法（只写 title 与 text 的 Modal）必须继续渲染，demo 里保留一处作回归样本
- 不引入第三方依赖，不新建包
- 删 set_languages 前全仓确认无其他调用点

## 任务清单

| ID | 任务 | 方式 | 涉及文件 / 模块 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 调色板与 QSS | 主 Agent | theme/{light,dark}/theme.py | 主题视觉规范、卡片描边 | - | 参考图取色一致，圆角 2，控件 32 | 完成 |
| T2 | 按钮与选择控件 | 主 Agent | components/{button,checkbox,radio,switch,tag}.py | 主题视觉规范 | T1 | 四种按钮、方形勾选与单选、实心标签 | 完成 |
| T3 | 输入与提醒 | 主 Agent | input.py、navitem.py、alert.py | 主题视觉规范 | T1 | 1px 边框、聚焦主色、浅底提醒 | 完成 |
| T4 | 字体 | 主 Agent | theme 两套 + app 注册 | 主题字体 | T1 | 应用字体与组件字体均为 HarmonyOS Sans SC | 完成 |
| T5 | 构建与验证 | 主 Agent | .theme、tests、verify | 全部 | T2,T3,T4 | 217 passed；verify light/dark 0 失败 | 完成 |
| T6 | 卡片选中态去对勾 | 主 Agent | theme/{light,dark}/components/card.py、tests/test_card.py、tests/test_choice.py | 选择容器与卡片 | - | 卡片不再有 QLabel 对勾，选中只改填充与描边；两组测试全绿 | 完成 |
| T7 | 浮层面板（light） | 主 Agent | theme/light/components/modal.py、theme/light/theme.py | 浮层、视觉统一 | - | 可放子组件、0..N 按钮、尺寸与拖拽、Esc 与遮罩、variant 三档均可用 | 完成 |
| T8 | 浮层面板镜像（dark） | subagent | theme/dark/components/modal.py、theme/dark/theme.py | 浮层、视觉统一 | T7 | 与 light 行为逐条一致，两种主题截图无差异 | 完成 |
| T9 | 关闭询问框复用面板 | 主 Agent | obox/ui/close_dialog.py、tests/test_settings_close.py | 浮层 | T7 | 无边框遮罩 QDialog，面板继承主题 QSS，choice 与 remember 语义不变 | 完成 |
| T10 | 标题栏去语言入口 | 主 Agent | obox/ui/title_bar.py、obox/ui/main_window.py、obox/app.py、tests/test_titlebar.py | i18n 注册与占位替换 | - | 标题栏只剩图标、标题与三个窗口按钮；switch_language 与设置页语言项仍可用 | 完成 |
| T11 | 示例片段改新写法 | 主 Agent | extensions/demo/views/main.oml、extensions/gallery/views/main.oml | 浮层 | T7,T8 | demo 保留旧写法样本，gallery 用容器与变体，装配无报错 | 完成 |
| T12 | verify_ui 场景与截图 | 主 Agent | scripts/verify_ui.py | 浮层、i18n 注册与占位替换、选择容器与卡片 | T9,T10,T11 | 语言改从设置页切，浮层补缩放与变体截图，两套主题 0 失败 | 完成 |
| T13 | 技能文档同步 | subagent | .agents/skills/obox-theme-dev、.agents/skills/obox-ui-test | 浮层、视觉统一 | T7,T9 | 契约写清容器/尺寸/关闭载荷，截图编号更新，标签数仍 21 | 完成 |
| T14 | 重编 pyd 与全量验证 | 后台 | .theme、tests、scripts/verify_ui.py | 浮层、选择容器与卡片、i18n 注册与占位替换、视觉统一 | T6,T8,T9,T10,T12,T13 | 关掉 obox 后重编两套 pyd，pytest 全绿，verify 两套主题 0 失败 | 完成 |

## 任务详情

### T6 卡片选中态去对勾

- 步骤：
  1. 删两套 card.py 里的 `self._check` QLabel、resizeEvent 里的定位与 set_selected 里的显隐，只保留填充与描边
  2. 在 tests/test_card.py 加一条断言：选中后子控件里不存在文本为 ✓ 的 QLabel，且 set_selected 前后 widget 的填充色变化
  3. 跑两组测试确认 CardComponent 与 ChoiceComponent 行为不变
- 验收命令：`uv run pytest -q tests/test_card.py tests/test_choice.py`（期望：全绿，退出码 0）
- 自检：单选、多选、独立卡片三种用法都还走得通；悬停描边仍只改颜色

### T7 浮层面板（light）

- 步骤：
  1. modal.py 拆标题区、正文容器、按钮区；container_layout 返回正文容器；面板直接子级的 Button 进按钮区并按声明顺序回传 value，其余子节点进正文容器
  2. 读 width/height 属性作初值，clamp 到 320×160 与视窗 90%；右下角 16×16 热区拖拽改尺寸
  3. Esc 与遮罩关闭按 close_on_esc / close_on_overlay 判断，close 载荷带 reason 与 value
  4. variant 取 info/confirm/danger，只换图标 badge 与主按钮色
  5. attach 改挂 host.window()，装 Resize 过滤器同步几何
  6. theme.py 补遮罩、按钮区、variant badge、缩放柄 QSS
- 验收命令：`uv run pytest -q tests/test_components.py`（期望：全绿），再跑 `uv run python scripts/verify_ui.py --theme light` 看浮层截图
- 断言清单：直接子级 Button 进按钮区、嵌套 Button 留在正文；三个 reason（button/esc/overlay）各一条；close_on_overlay 默认关；width 缺省 420、拖拽 clamp 到 320×160 与宿主窗口 90%；variant 三档只差图标与主按钮色；只写 title 与 text 时仍出一个按钮
- 自检：只写 title 与 text 的旧片段仍渲染标题+正文+一个按钮；close 载荷三个 reason 都对

### T8 浮层面板镜像（dark）

- 步骤：
  1. 照 T7 的 light 实现逐段镜像到 theme/dark/components/modal.py
  2. theme/dark/theme.py 补同名 QSS，只换色值
  3. 对比两套主题下浮层的尺寸、圆角、按钮排布
- 验收命令：`uv run pytest -q tests/test_components.py tests/test_kit_switch.py`（期望：全绿）
- 自检：行为差异为零，只有颜色不同；dark 下变体图标对比度足够

### T9 关闭询问框复用面板

- 步骤：
  1. close_dialog.py 改无边框 + 半透明遮罩的 QDialog，几何对齐父窗口
  2. 内嵌对象名 obox-modal-card 的面板与 obox-modal-title / obox-modal-body 文案位
  3. 保留记住勾选与三按钮，Esc 等同取消
- 验收命令：`uv run pytest -q tests/test_settings_close.py tests/test_close_action.py`（期望：全绿）
- 自检：choice 与 remember 字段语义不变；父窗口为空时仍能显示（内联兜底样式）

### T10 标题栏去语言入口

- 步骤：
  1. title_bar.py 删语言按钮、language_requested 信号、set_language_label，_on_button 同步收缩
  2. main_window.py 删 set_languages、_open_language_menu、_choose_language 与相关字段
  3. app.py 删 _language_choices 与 _sync_languages 及其两处调用，switch_language 保留
  4. tests/test_titlebar.py 补一条断言：标题栏子控件里没有语言按钮
- 验收命令：`uv run pytest -q tests/test_titlebar.py tests/test_i18n_switch.py tests/test_settings_filter.py`（期望：全绿）
- 自检：设置页语言项仍能切换并重建视图；--lang 启动仍生效；全仓无 set_languages 残留调用

### T11 示例片段改新写法

- 步骤：
  1. gallery 的浮层改成容器写法（正文子组件 + 两个按钮 + 一个 variant 示例）
  2. demo 的浮层改成新写法，另留一处只写 title 与 text 的旧写法作兼容样本
  3. 装配两个扩展确认不报错
- 验收命令：`uv run pytest -q tests/test_builder.py tests/test_e2e.py`（期望：全绿）
- 自检：旧写法样本仍在且能打开；按钮 value 在 close 事件里能拿到

### T12 verify_ui 场景与截图

- 步骤：
  1. 语言场景改从设置页触发，删标题栏按钮相关步骤
  2. 浮层补拖拽缩放、variant 三档、Esc 与遮罩关闭的截图
  3. 卡片选中截图确认无对勾
- 验收命令：`uv run python scripts/verify_ui.py --theme light` 与 `uv run python scripts/verify_ui.py --theme dark`（期望：两条都以 0 失败结束）
- 自检：截图编号连续无空洞；语言场景不依赖标题栏

### T13 技能文档同步

- 步骤：
  1. obox-theme-dev 的 component-contract 写清 modal 的容器、尺寸、关闭载荷与 variant
  2. obox-ui-test 的 scenarios 更新截图编号与浮层场景
  3. 确认标签计数仍为 21，两处文档一致
- 验收命令：`uv run python .agents/skills/obox-test/scripts/check_all.py`（期望：退出码 0）
- 自检：契约描述与代码一致，没有残留旧参数说明

### T14 重编 pyd 与全量验证

- 步骤：
  1. 关闭正在运行的 obox（Windows 会锁文件）
  2. 重编两套主题，跑全量测试
  3. 跑两套主题的界面验证
- 验收命令：`uv run python scripts/build_theme.py light dark && uv run pytest -q && uv run python scripts/verify_ui.py --theme light && uv run python scripts/verify_ui.py --theme dark`（期望：全绿，verify 0 失败）
- 自检：.theme 里的 pyd 时间戳是本次；verify 截图里卡片无对勾、浮层圆角 2px

## 测试策略

TDD：每任务至少先有失败测试，验收命令包含对应 pytest；测试只写在现有 seam（components 构造、Builder 装配、MainWindow/CloseDialog 行为）上，期望值取自 delta-spec 的场景。

## 执行顺序

1. T6 ∥ T7 ∥ T10
2. T8 ∥ T9
3. T11
4. T12 ∥ T13
5. T14

## 覆盖检查

- 浮层：T7、T8、T9、T11、T12、T13、T14
- 选择容器与卡片：T6、T12、T14
- i18n 注册与占位替换：T10、T12、T14
- 视觉统一：T7、T8、T13、T14

## 自检（落盘前）

- [x] 每条需求都被至少一个任务覆盖
- [x] 每个任务都有可复制执行的验收命令
- [x] 依赖无环，且没有"同文件无依赖"的并行任务
- [x] 方式只取 主 Agent / subagent / 后台
- [x] 模板占位与注释已全部替换