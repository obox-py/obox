---
status: done
---

# UI 框架与扩展系统 Delta Spec

## ADDED Requirements

### Requirement: 主界面三段布局

obox SHALL 按上、中、下三段组织主界面：顶栏左侧显示 obox 图标与名称、右侧提供最小化、最大化与关闭；中部左侧为只显示图标的侧栏并兼作扩展注册点，右侧为内容区；底部为扩展注册区，没有扩展注册时隐藏。

#### Scenario: 扩展注册到侧栏

- **WHEN** 扩展在清单中声明一个侧栏视图并带 svg 图标
- **THEN** 侧栏出现该扩展的图标，点击后内容区显示该扩展的视图

#### Scenario: 顶栏窗口按钮

- **WHEN** 用户点击顶栏右侧的最小化、最大化或关闭按钮
- **THEN** 窗口执行对应动作，关闭时退出主程序并回收扩展宿主

#### Scenario: 扩展注册到底部栏

- **WHEN** 扩展在清单中声明底部栏视图
- **THEN** 底部栏显示该扩展提供的组件；没有扩展注册时底部栏不占空间


### Requirement: 界面套件清单与加载

obox SHALL 扫描 .theme 下每个子目录，读取其中的 theme.json（name、version、mode、entry）与 pyd，形成可用套件清单；启动时按该清单与 .obox/config.json 的 theme 字段选择一套（配置缺失时取 light），命令行参数可以临时覆盖；缺清单、缺 pyd 或版本不兼容时报错退出。设置界面里的套件选择留到下一轮。

#### Scenario: 启动时枚举可用套件

- **WHEN** .theme 下同时存在 light 与 dark 两个子目录，且各自有 theme.json 与 pyd
- **THEN** obox 得到包含两者的可用套件清单，并按配置或默认值选中 light

#### Scenario: 按配置加载 light

- **WHEN** .obox/config.json 的 theme 为 light，且 .theme/light 下有 light.pyd 与 theme.json
- **THEN** obox 加载该 pyd 并用 light 套件渲染主界面

#### Scenario: 缺失即失败

- **WHEN** .theme/light 下没有 pyd 文件
- **THEN** 启动失败并给出指明缺失路径的错误，不进入主窗口

#### Scenario: 版本不兼容

- **WHEN** theme.json 声明的版本与 obox 期望的契约版本不匹配
- **THEN** obox 拒绝加载该套件并报告版本号

### Requirement: 界面提供者契约

kit SHALL 通过入口工厂返回 provider，暴露标签到组件类的映射、套件元信息（名称、模式、版本）与主题 QSS；组件类的构造签名与现有 15 个组件一致。

#### Scenario: 工厂可用

- **WHEN** 加载某个 kit 的 pyd 并调用清单声明的入口函数
- **THEN** 得到包含 15 个标签的映射，标签小写后与现有取值一致

#### Scenario: 主题可取

- **WHEN** 询问 provider 的主题 QSS
- **THEN** 返回同时覆盖外壳与组件的样式文本，应用后外观生效

### Requirement: 组件契约不变

两套 kit SHALL 提供与现有实现一致的标签名、状态名与事件名，扩展片段无需改动即可在任意一套下渲染。

#### Scenario: 同一片段在两套 kit 下都渲染

- **WHEN** 用 demo 扩展的片段分别在 light 与 dark 下装配
- **THEN** 两次都成功，组件 id 与标签一致

#### Scenario: 未知标签仍报错

- **WHEN** 片段里出现未注册的标签
- **THEN** 装配失败，错误信息包含标签名与所在行列

### Requirement: 视觉统一

每套 kit SHALL 提供统一主题：圆角取 10px 量级、边框为 1px 淡色或去掉、阴影为无或大模糊低透明；切换套件后外壳与内容区同时变化。

#### Scenario: 圆角与边框

- **WHEN** 渲染任意一套 kit 的卡片与输入类组件
- **THEN** 圆角与边框取值来自该套件的主题常量，而不是 qfluentwidgets 默认值

#### Scenario: 切换后整体变化

- **WHEN** 从 light 切到 dark
- **THEN** 顶栏、侧栏、底部栏与内容区一起变为深色

### Requirement: 运行中切换 kit

obox SHALL 支持运行中切换套件：销毁现有视图并按新套件重建；新套件加载失败时保留原套件并报错。

#### Scenario: 切换成功

- **WHEN** 请求从 light 切换到 dark 且 dark 可加载
- **THEN** 现有视图被销毁并重建，外观变为深色，组件 id 重新注册

#### Scenario: 切换失败回滚

- **WHEN** dark 的 pyd 损坏或清单不合法
- **THEN** 保留 light 的视图并给出错误提示，进程不退出

### Requirement: 构建与 pyd 产物

工程 SHALL 提供一条构建命令，把 theme/{name} 编译为 .theme/{name}/{name}.pyd 并复制 theme.json；构建失败以非零退出码结束且不留半成品。

#### Scenario: 构建产物齐全

- **WHEN** 执行构建命令
- **THEN** .theme/light 下同时出现 light.pyd 与 theme.json

#### Scenario: 构建失败

- **WHEN** 源码存在语法错误或缺少编译器
- **THEN** 退出码非零，错误信息指明原因，且不留下不完整的产物目录

### Requirement: 组件能力接口与消息处理分界

kit 的组件 SHALL 声明 supported_states 与 state_accessors（状态名到读取与写入方法名的映射）、supported_events 与 event_methods（事件名到注册方法名的映射）；obox SHALL 保留消息构造、注册表、路由、越权判断与应答，并通过这些映射调用 kit 的方法，且只把片段里用 on_ 前缀属性声明过的事件绑定回调。

#### Scenario: 状态查询经映射

- **WHEN** 扩展查询某输入框的 value，且该组件的 state_accessors 把 value 映射到读取方法 text
- **THEN** obox 调用 text 得到当前文本，并以应答消息回传，kit 内部方法命名不受 obox 约束

#### Scenario: 状态修改经映射

- **WHEN** 扩展修改该输入框的 value
- **THEN** obox 调用映射里的写入方法并返回成功，组件显示新值

#### Scenario: 事件经具名方法注册

- **WHEN** 扩展创建的按钮被点击
- **THEN** kit 触发已注册的点击回调，obox 据此构造 ComponentEventMessage 并投递给该扩展

#### Scenario: 不支持的状态被拒绝

- **WHEN** 扩展查询组件的 supported_states 之外的状态
- **THEN** obox 返回明确的不支持错误，不调用 kit

### Requirement: 测试链路

测试 SHALL 以内存假 provider 为主，另有一条加载真实 pyd 的集成用例验证工厂、清单与标签映射。

#### Scenario: 假 provider 跑常规用例

- **WHEN** 执行常规测试且未构建任何 pyd
- **THEN** 用例通过，装配与外观点用假 provider

#### Scenario: 真实 pyd 集成用例

- **WHEN** 执行集成用例且 .theme/light 下存在 pyd
- **THEN** 用例加载它并断言 15 个标签与元信息

## ADDED Requirements（第五轮：移除第三方控件库）

### Requirement: 不依赖第三方控件库

工程 SHALL 只依赖 PySide6：控件库提供的按钮、输入、选择、滑块、表格、页签、开关、复选框、单选、标签、通知与浮层全部由纯 Qt 控件或自绘图元实现，pyproject 不再声明 PySide6-Fluent-Widgets，代码中不出现其导入。

#### Scenario: 依赖清单

- **WHEN** 查看 pyproject 的 dependencies
- **THEN** 只有 PySide6，没有 PySide6-Fluent-Widgets

#### Scenario: 代码导入

- **WHEN** 全仓搜索 qfluentwidgets
- **THEN** 没有任何 Python 文件导入它

#### Scenario: 外观不回退

- **WHEN** 以 light 与 dark 打开组件画廊
- **THEN** 按钮、输入、选择、滑块、表格、页签、开关等外观与替换前一致或更接近主题

### Requirement: 控件过渡动画

组件 SHALL 在状态切换时带短促过渡：开关滑块滑动、复选框打勾淡入、单选圆点放大、按钮悬停与按下的底色过渡、提醒条与通知淡入、模态浮层淡入；过渡时长 90 到 220 毫秒，不阻塞消息处理。

#### Scenario: 开关切换
- **WHEN** 点击开关
- **THEN** 滑块在 170 毫秒内滑到另一端，轨道颜色同步过渡

#### Scenario: 复选与单选
- **WHEN** 点击复选框或单选按钮
- **THEN** 对勾或圆点在 140 毫秒内淡入/放大

#### Scenario: 按钮悬停
- **WHEN** 鼠标移入或移出按钮
- **THEN** 底色在 140 毫秒内过渡到悬停色或退回原色，按下时再压暗一点

#### Scenario: 浮层出现
- **WHEN** 提醒条、通知或模态被设为可见
- **THEN** 以淡入方式出现，不闪一下

### Requirement: i18n 注册与占位替换

扩展与 obox 主窗体 SHALL 能注册多语言文案：扩展的文案写在扩展目录的 i18n.json（数组，条目为 id、lang、value；id 以小写字母开头、可含数字与点），obox 自身同样用 i18n.json；注册参数为 name（扩展标识 名称.作者，主窗体为 obox）、id 与 values（BCP-47 到文案的字典，必须含 zh-CN）；视图片段中的 i18n 引用（双花括号包住 i18n 与条目 id） SHALL 在渲染前替换为当前语言文案，缺当前语言时回退 zh-CN，未注册的引用原样保留。obox SHALL 在标题栏提供语言切换入口，切换后自动重建全部视图与外壳文案，并把选择写入配置。

#### Scenario: 注册并替换
- **WHEN** 扩展注册 id 为 title、values 含 zh-CN 与 en-US，oml 里写 i18n.title 占位符
- **THEN** 当前语言为 zh-CN 时渲染中文，切到 en-US 时渲染英文

#### Scenario: 回退
- **WHEN** 当前语言在 values 里没有对应项
- **THEN** 使用 zh-CN 的文案

#### Scenario: 手动切换语言
- **WHEN** 从标题栏菜单选择另一种语言
- **THEN** 界面文案立即切换，视图按新语言重建，选择写入 .obox/config.json

#### Scenario: 越权与缺省
- **WHEN** 扩展注册的 name 不是自己，或 values 缺 zh-CN
- **THEN** 注册被拒绝并记录原因

### Requirement: 视图文件格式

扩展 SHALL 通过相对扩展目录的 .oml 文件路径注册视图，而不是把片段文本直接传过去；obox 读取该文件（路径越出扩展目录或文件缺失即失败且不挂载视图）并按 obox 组件语法渲染，渲染前完成 i18n 替换。

#### Scenario: 从 oml 渲染
- **WHEN** 扩展注册视图时给出 views/main.oml
- **THEN** obox 读取该文件并装配出控件树

#### Scenario: 越界与缺失
- **WHEN** 路径写成 ../secret.oml，或文件不存在
- **THEN** 视图不挂载，界面提示加载失败

## MODIFIED Requirements

### Requirement: 组件事件上报

obox SHALL 只在 HTML 片段用 on_ 前缀属性声明了回调时才投递组件事件；未声明的事件在装配阶段就不绑定回调，交互不会产生任何消息。

#### Scenario: 声明后点击才投递

- **WHEN** 片段的按钮带 on_click 属性
- **THEN** 点击时该扩展收到 ComponentEventMessage，载荷仍是组件 id 与事件名

#### Scenario: 未声明则不投递

- **WHEN** 片段的按钮没有 on_click 属性
- **THEN** 点击不会产生组件事件消息，obox 侧直接跳过

#### Scenario: 声明了组件不支持的事件

- **WHEN** 片段写了该组件 supported_events 之外的 on_ 属性
- **THEN** 装配失败并指出具体属性与所在行

## Impact

- 兼容性：无既有行为需要保留或迁移，工程此前只有入口脚本。
- 下游影响：task.md 的需求覆盖以基线 13 条与两条 delta 需求（主界面三段布局、可替换组件库）为准；收尾时把 ADDED 并入基线、把 MODIFIED 的「组件事件上报」整节替换。
- 兼容性：已有片段若没有 on_ 属性，将不再收到事件，demo 需要补写 on_click；消息载荷保持不变，仍只有组件 id 与事件名。