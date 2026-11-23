---
status: done
---

# 主题视觉美化 Spec Delta

## Purpose

迭代一的差异（主题视觉规范、主题字体、卡片描边）已合并进基线，不再重复。本次只写与当前基线的差异：卡片选中不显示对勾、新增覆盖组件与系统询问框的浮层需求、语言切换入口从标题栏移到设置页、视觉统一的圆角与边框口径收敛到现状。

## ADDED Requirements

### Requirement: 浮层

浮层 SHALL 由半透明遮罩与居中面板组成：面板分标题区、正文区与按钮区，正文区可放任意子组件，按钮区按声明顺序放 0 到 N 个按钮——面板的直接子级 Button 进按钮区，其余子节点进正文区，正文内嵌套的 Button 保持原位；width、height 属性给出初始尺寸，缺省宽 420、高随内容，下限 320×160，上限为宿主窗口的 90%，内容超出时正文区滚动；面板右下角 16×16 区域 SHALL 可拖拽调整尺寸。浮层可由按钮、Esc、点击遮罩三种方式关闭：close_on_esc 缺省为真、close_on_overlay 缺省为假，两者均可改；关闭时投递 close 事件，携带 reason（button、esc、overlay）与来源按钮的 value。没有子组件的浮层 SHALL 退化为标题、正文与一个"知道了"按钮，旧片段照常渲染。variant 取 info、confirm、danger，只改变左侧图标与主按钮配色，三档布局一致。系统级关闭询问框 SHALL 使用同一套面板与按钮排布，并保留"记住我的选择"勾选与三个按钮。

#### Scenario: 正文放任意组件与自定义按钮

- **WHEN** 扩展在 Modal 内写输入框、文本与两个 Button
- **THEN** 三者按顺序渲染在正文区，点击按钮关闭浮层，close 事件带该按钮的 value

#### Scenario: 旧写法继续可用

- **WHEN** 片段只写 title 与 text 两个属性
- **THEN** 面板显示标题、正文与一个"知道了"按钮，点击后关闭并投递 close

#### Scenario: 初始尺寸与拖拽边界

- **WHEN** 不写 width、height 就打开浮层，再把右下角拖到超过视窗
- **THEN** 初次打开宽 420、高随内容；拖拽后尺寸停在宿主窗口的 90%，内容超出时正文区出现滚动

#### Scenario: 三种关闭来源

- **WHEN** 分别按 Esc、点击遮罩、点击按钮
- **THEN** close 事件的 reason 依次为 esc、overlay、button；把 close_on_overlay 设为真后点遮罩才关闭

#### Scenario: 变体只差图标与按钮色

- **WHEN** 三个浮层分别声明 variant 为 info、confirm、danger
- **THEN** 标题、正文与按钮位置一致，只有左侧图标与主按钮配色不同

#### Scenario: 系统询问框同一套面板

- **WHEN** 关闭窗口且 obox.close_action 为 ask
- **THEN** 询问框与扩展浮层共用同一套面板尺寸、圆角与按钮排布，含"记住我的选择"与三个按钮

## MODIFIED Requirements

### Requirement: 选择容器与卡片

改自基线 spec.md「选择容器与卡片」，删掉"右下角显示对勾"。

选择容器 SHALL 支持 mode 为 single 或 multiple，内部放若干卡片；卡片用 value 标识，内部可放任意自定义组件；被选中的卡片以 ACCENT_SOFT 底色与 1px 主色描边表示，悬停时只改变描边颜色，不显示对勾或其他标记；容器暴露 value（选中 value 的列表）并投递 change 事件；单选允许再次点击清空。卡片 SHALL 也可独立使用：不放进选择容器时按普通容器展示自定义内容，声明 on_click 后点击投递 click 事件，悬停时描边变强调色。

#### Scenario: 选中只变色

- **WHEN** 在多选容器里点中一张卡片
- **THEN** 卡片变为 ACCENT_SOFT 底色与主色 1px 描边，右下角不出现对勾或任何标记

#### Scenario: 独立使用卡片

- **WHEN** 片段写一个不在 Choice 内的 Card，内含若干组件并声明 on_click
- **THEN** 卡片按普通容器展示内容，点击时投递 click 事件，悬停时描边变色

#### Scenario: 多选切换

- **WHEN** 容器 mode 为 multiple，依次点击两张卡片
- **THEN** 两张都被选中，value 返回两个 value，且每次点击都投递 change 事件

#### Scenario: 单选互斥与清空

- **WHEN** 容器 mode 为 single，点击另一张卡片，再点同一张
- **THEN** 选中项先切换到新卡片，再次点击后清空

### Requirement: i18n 注册与占位替换

改自基线 spec.md「i18n 注册与占位替换」，把标题栏入口改为设置页入口。

扩展与 obox 主窗体 SHALL 能注册多语言文案：扩展的文案写在扩展目录的 i18n.json（数组，条目为 id、lang、value；id 以小写字母开头、可含数字与点），obox 自身同样用 i18n.json；注册参数为 name（扩展标识 名称.作者，主窗体为 obox）、id 与 values（BCP-47 到文案的字典，必须含 zh-CN）；视图片段中的 i18n 引用（双花括号包住 i18n 与条目 id）SHALL 在渲染前替换为当前语言文案，缺当前语言时回退 zh-CN，未注册的引用原样保留。obox SHALL 只把语言切换入口放在设置页，标题栏不放置语言切换控件；切换后自动重建全部视图与外壳文案，并把选择写入配置。

#### Scenario: 注册并替换

- **WHEN** 扩展注册 id 为 title、values 含 zh-CN 与 en-US，oml 里写 i18n.title 占位符
- **THEN** 当前语言为 zh-CN 时渲染中文，切到 en-US 时渲染英文

#### Scenario: 从设置页切换语言

- **WHEN** 在设置页的界面语言项里选择另一种语言
- **THEN** 界面文案立即切换，视图按新语言重建，选择写入 .obox/config.json，标题栏不出现语言按钮

#### Scenario: 越权与缺省

- **WHEN** 扩展注册的 name 不是自己，或 values 缺 zh-CN
- **THEN** 注册被拒绝并记录原因

### Requirement: 视觉统一

改自基线 spec.md「视觉统一」，圆角与边框口径收敛到主题视觉规范的现状。

每套套件 SHALL 提供统一主题：层级用背景色差、字号与留白建立；输入类控件与卡片默认带 1px 淡边框（#e2e5eb / #31343b），其它控件默认不描边；控件与浮层圆角 2px；不使用阴影；切换套件后外壳与内容区同时变化。

#### Scenario: 圆角与边框

- **WHEN** 渲染任意一套套件的输入框、卡片与浮层
- **THEN** 三者圆角均为 2px，输入框与卡片带 1px 淡边框，浮层无阴影

#### Scenario: 切换后整体变化

- **WHEN** 从 light 切到 dark
- **THEN** 顶栏、侧栏、底部栏与内容区一起变为深色

## Impact

- 兼容：demo 与 gallery 的旧 Modal 片段无需修改即可渲染，自动带"知道了"按钮
- 破坏：选中卡片不再有对勾，依赖该标记的截图与 verify_ui 场景要更新
- 破坏：标题栏语言按钮与其菜单路径删除，MainWindow.set_languages 一并移除；switch_language 与设置页语言项保留，verify_ui 仍可切换
- 视觉统一改口径后，历史截图的圆角与边框描述作废，验证以新口径为准
- 组件标签数仍是 21，modal 契约扩大，需同步 obox-theme-dev 与 obox-ui-test
