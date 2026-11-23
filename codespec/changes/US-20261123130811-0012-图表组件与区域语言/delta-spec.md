---
status: done
---

# 组件归位与区域语言 Spec Delta

## Purpose

把 UI 组件从主题包迁到 obox，让主题只承担样式；新增可交互的 matplotlib 图表组件；语言从两档升级为 BCP-47 地区并在缺失时按语言基码回退。

## ADDED Requirements

### Requirement: 图表组件

obox SHALL 提供 chart 组件（标签 chart）：接受 JSON 数据：type 取 line、bar、scatter；series 为数组，每项形如 {name, points: [{x, y}]}；x 标签可选；title 可选，用 matplotlib 的 QtAgg 画布嵌入视图，不经过网页渲染。chart SHALL 支持滚轮缩放、按住拖动平移、悬停显示当前坐标、右上角重置视图。数据由扩展进程经消息下发，跨进程只传 JSON，不传绘图对象。

#### Scenario: 渲染折线图

- **WHEN** 扩展把 data 状态设为 type=line 的两条 series
- **THEN** 视图出现一张折线图，坐标轴与图例按数据渲染

#### Scenario: 缩放与重置

- **WHEN** 在图上滚轮缩放后点重置
- **THEN** 视图回到初始范围，缩放与平移被撤销

#### Scenario: matplotlib 未安装

- **WHEN** 运行环境缺少 matplotlib
- **THEN** chart 区域显示「未安装 matplotlib」的提示，其它组件正常

#### Scenario: 跨进程数据

- **WHEN** 扩展在宿主进程里更新 data
- **THEN** obox 的图表按新数据重绘，宿主进程不持有任何 matplotlib 对象

### Requirement: 区域语言与缺省回退

obox SHALL 按 BCP-47 解析当前语言：先精确匹配已注册的条目，未命中时按语言基码回退（zh-* 回退 zh-CN、en-* 回退 en-US），仍未命中回退 zh-CN。扩展与 obox 主窗体的 i18n 注册 SHALL 必须包含 zh-CN，缺失时拒绝注册并记录原因；运行期展示的语言列表 SHALL 为 Qt 可枚举的全部地区，每项以其原生地区名显示（zh-CN → 中国大陆、en-US → America），并支持按名称搜索（搜索框既过滤分类与条目标题，也过滤语言下拉的候选项，命中后下拉只显示匹配地区）。

#### Scenario: 香港中文回退

- **WHEN** 当前语言为 zh-HK，而扩展只注册了 zh-CN
- **THEN** 界面显示 zh-CN 文案，不回退到英文，也不显示占位原文

#### Scenario: 英国英语回退

- **WHEN** 当前语言为 en-GB，而扩展只注册了 en-US 与 zh-CN
- **THEN** 界面显示 en-US 文案

#### Scenario: 缺 zh-CN 被拒

- **WHEN** 扩展注册的 values 只有 en-US
- **THEN** 注册被拒绝并记录原因，界面回退到 obox 的 zh-CN 文案

#### Scenario: 语言项显示原生名

- **WHEN** 打开设置的语言项
- **THEN** 下拉里是全部地区，zh-CN 显示为「中国大陆」、en-US 显示为「America」，可搜索

## MODIFIED Requirements

### Requirement: 界面套件清单与加载

改自基线「界面套件清单与加载」：主题只提供样式。

obox SHALL 从 .theme 加载主题套件；套件清单 SHALL 声明名称、版本、模式、调色板、字体目录、图标色与间距，并交付 styles.qss（键名用双花括号包裹，引用调色板取值）；obox 加载后把 TOKEN 替换为调色板取值并注入；套件不再提供组件类，组件由 obox 自己实现。加载时校验清单字段与样式能力，缺少必需字段即报错并保留当前套件。

#### Scenario: QSS 以文件交付

- **WHEN** 查看 theme/light 目录
- **THEN** 有 styles.qss，内容里的大写键用双花括号包裹，加载后得到实际色值

#### Scenario: 主题只有样式

- **WHEN** 切换 light 与 dark
- **THEN** 组件实现不变，只换 QSS、调色板与字体

### Requirement: 组件契约不变

改自基线「组件契约不变」：组件由宿主提供。

两套主题 SHALL 只通过样式影响组件外观；21 个组件标签 + chart 由 obox 提供唯一实现，扩展片段在任意主题下渲染出的组件类型、状态名与事件名一致。

#### Scenario: 同一片段在两套主题下都渲染

- **WHEN** 用 demo 扩展的片段分别在 light 与 dark 下装配
- **THEN** 两次都成功，组件 id、标签与状态映射一致，只有样式不同

### Requirement: 组件能力接口与消息处理分界

改自基线「组件能力接口与消息处理分界」：宿主组件同样声明能力表。

obox SHALL 为其提供的组件声明 supported_states 与 state_accessors、supported_events 与 event_methods，并通过类型化方法实现读写；扩展查询与修改仍经消息路由、越权判断与应答，宿主组件的实现细节不出现在契约里。

#### Scenario: 宿主组件的状态查询

- **WHEN** 扩展查询 chart 的 data 状态
- **THEN** obox 走同一套状态查询通道返回数据，chart 的实现细节不外露

### Requirement: 主题色板与文字层级

改自基线「主题色板与文字层级」：调色板成为组件绘制颜色的唯一来源。

每套主题 SHALL 通过调色板暴露颜色、圆角与控件高度：主色与强调淡底、页面与卡片底色、边框与分隔线、文字与辅助文字、危险与成功色；组件自绘时 SHALL 从调色板取值，不内置十六进制常量。主题的 QSS SHALL 与调色板取值一致。

#### Scenario: 两套主题的组件取色

- **WHEN** 在 light 与 dark 下查看同一个按钮
- **THEN** 颜色来自各自调色板，形状与尺寸一致

### Requirement: i18n 注册与占位替换

改自基线「i18n 注册与占位替换」：补区域回退与强制缺省。

扩展与 obox 主窗体 SHALL 能注册多语言文案（扩展写在 i18n.json，主窗体同为 i18n.json），注册必须含 zh-CN；视图片段中的 i18n 引用 SHALL 在渲染前按「精确匹配 → 语言基码回退 → zh-CN」解析；obox SHALL 在设置页提供语言切换入口，选项为 Qt 可枚举的全部地区并显示原生地区名，切换后重建视图并把选择写入配置。

#### Scenario: 注册并替换

- **WHEN** 扩展注册 zh-CN 与 en-US，片段写 i18n.title
- **THEN** zh-CN 下显示中文，切到 en-US 显示英文

#### Scenario: 未覆盖的地区回退

- **WHEN** 当前语言为 zh-TW，扩展只注册 zh-CN 与 en-US
- **THEN** 显示 zh-CN 文案

### Requirement: 设置扩展

改自基线「设置扩展」：语言项改为全量地区。

工程 SHALL 提供系统扩展 extensions/settings：侧栏视图、左侧分类、右侧设置项、顶部搜索；语言项 SHALL 列为 Qt 可枚举的全部地区，以原生地区名显示并支持搜索；选中后立即切换语言并持久化。

#### Scenario: 语言项可搜索

- **WHEN** 在设置搜索框输入「中国」
- **THEN** 语言项筛出中文相关地区，选择后界面切到该地区

## Impact

- 主题包结构变化：不再含 components 目录，改为 styles + palette；打包脚本与 pyd 内容随之变
- 组件契约由「套件提供」改为「宿主提供」，REQUIRED_TAGS 的含义从套件必备变为宿主必备，校验与文档都要改
- 新增运行时依赖 matplotlib（约 50MB）；matplotlib 未安装时 chart 显示「未安装」提示，不抛异常
- 旧主题 pyd 若仍带 component_types，加载时忽略该字段并记一条「请重编主题」日志，不阻止启动
- i18n 回退与强制 zh-CN 影响所有扩展与 obox 自身的 i18n.json
- 设置语言项由两档变为全量地区，配置里存的是具体地区