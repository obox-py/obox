---
status: done
---

# obox 界面框架与扩展系统 Specification

## Purpose

obox 是一个用 Python 与 PySide6 构建的可扩展桌面程序（界面控件为纯 Qt 与自绘，不依赖第三方组件库）。本规格定义扩展如何声明界面与行为、obox 如何装配这些界面、双方如何通过消息协作，以及扩展如何被发现与激活，让第三方只写 Python 与静态资产，就能交付带界面的功能扩展，而不必触碰 obox 的内部实现。

## Requirements
### Requirement: 主题视觉规范

light 与 dark 套件 SHALL 按参考图统一视觉：主色 #2f6bee / #5b8def，页面与卡片底色、分隔线、文字与辅助文字分级，控件圆角 2px、控件高度 32，按钮区分 primary/secondary/ghost/danger，复选框与单选为方形，标签实心主色、label 为灰底。

#### Scenario: 两套主题一致
- **WHEN** 切换 light 与 dark
- **THEN** 同一组件的形状、间距一致，只换颜色

### Requirement: 主题字体

每个套件 SHALL 指定并使用自己 fonts 目录中的 HarmonyOS Sans SC：QSS 首选该族，应用启动时注册该套件字体并设为应用字体，缺字回退 Noto Sans SC 与 Microsoft YaHei UI。

#### Scenario: 组件使用鸿蒙字体
- **WHEN** 打开任意视图
- **THEN** 文本按 HarmonyOS Sans SC 渲染，切换套件后仍使用该套件字体

### Requirement: 卡片描边

卡片组件 SHALL 在 light 与 dark 两套套件中绘制四边等宽、圆角 2px 的 1px 描边：描边中心对齐整数设备像素（按 devicePixelRatio 计算内缩），颜色 #e2e5eb / #31343b；选中与悬停时用主色描边。

#### Scenario: 四边等宽
- **WHEN** 显示任意卡片
- **THEN** 左右与上下描边宽度一致，圆角处无缺口或加粗

### Requirement: 标题栏窗口按钮

标题栏最小化、最大化/还原、关闭按钮 SHALL 使用自绘矢量图标（12x12 绘制区，按钮 40x30）：颜色随主题 muted/active 变化，悬停有底色，关闭悬停为红底白线；最大化状态显示还原图标。

#### Scenario: 清晰可辨
- **WHEN** 查看标题栏三个按钮
- **THEN** 线条清晰、尺寸一致，悬停与最大化切换可见

### Requirement: 界面缩放与清晰度

obox SHALL 在 Windows 高 DPI 下使用 PassThrough 缩放策略：窗口按 devicePixelRatio 渲染，标题栏图标与图标位图按 DPR 生成，自绘线条对齐设备像素，避免发虚与描边断续。

#### Scenario: 150% 缩放
- **WHEN** 系统缩放为 150% 时启动 obox
- **THEN** 文字与自绘线条清晰，卡片描边四边连续等宽

### Requirement: 模板指令与值绑定

OML 与内联片段 SHALL 支持 o-for、o-if 与值绑定：o-for="item in items" 按列表重复元素（作用域内可用 item 与 index），o-if="expr" 按条件渲染；双花括号包裹的表达式在文本与属性中绑定数据；表达式支持点路径、length、字面量与 ==、!=、>、<、! 比较；i18n 引用优先解析，未解析的保持原样。

#### Scenario: 列表与条件
- **WHEN** 片段写 o-for 遍历三项并配合 o-if
- **THEN** 渲染三份元素，条件不成立时不渲染

### Requirement: 视图数据与局部更新

扩展注册视图时 SHALL 能提供初始 data；obox SHALL 能注入或更新视图数据，更新时只刷新受影响部分：文本与属性绑定原地改写，o-for 与 o-if 区域按其容器重建。

#### Scenario: 列表变化
- **WHEN** 视图数据里的列表从三项变成两项
- **THEN** 只重建该 o-for 区域，其它组件实例保持不变

### Requirement: 视图生命周期

视图 SHALL 在渲染完成与销毁时向所属扩展投递 mounted 与 unmounted 事件，携带 view_id。

#### Scenario: 挂载与销毁
- **WHEN** 视图被装配并显示，随后切走并销毁
- **THEN** 扩展依次收到 mounted 与 unmounted

### Requirement: 应用注册

扩展 SHALL 在 extension.json 的 contributes.app 里注册一个或多个应用；每项可声明 id、title、icon、single、persistent：id 缺省 {扩展标识}.app（数组按下标追加序号），icon 是相对 assets 目录的 svg 且原样显示、不做单色重染，single 缺省 true，persistent 缺省 false 且仅在 single 为 true 时生效。

#### Scenario: 多应用与图标
- **WHEN** 扩展用数组声明两个应用并给 icon
- **THEN** 两个应用都被识别，网格里原样显示各自图标

### Requirement: 应用页作为系统扩展

应用页 SHALL 由仓库内的真实扩展 extensions/app 提供（name=app、publisher=obox、version=1.0.0）；该扩展只注册左侧边栏视图，不声明 contributes.app，因此不出现在应用网格里。

#### Scenario: 自身不进网格
- **WHEN** 查看应用网格
- **THEN** 只出现声明了 contributes.app 的扩展，app.obox 不在其中

### Requirement: 应用搜索

应用页 SHALL 提供搜索框：输入时按应用标题、扩展描述与作者做不区分大小写的子串匹配，过滤网格卡片；查询为空时显示全部；过滤由 App 扩展执行，结果通过 APP_VIEW_DATA_MSG 回注，obox 只接受该视图 owner 发来的消息与已知应用；扩展增删后列表自动同步。

#### Scenario: 子串过滤
- **WHEN** 在搜索框输入「笔」
- **THEN** 只保留标题、描述或作者含「笔」的卡片，清空后恢复全部

#### Scenario: 扩展增删后同步
- **WHEN** 运行中新增或卸载扩展
- **THEN** 宿主重启、列表重算并推回 App 扩展，卡片随之更新

### Requirement: 应用网格

obox SHALL 用网格卡片列出所有声明了 app 的已激活扩展：卡片左侧图标，右侧两行（应用标题、作者与版本），下方描述；卡片由 o-for 遍历 apps 数据生成。

#### Scenario: 卡片内容
- **WHEN** 打开应用页
- **THEN** 每个应用一张卡片：左侧图标、右侧标题与作者版本、下方描述

### Requirement: 打开应用与窗口复用

点击卡片 SHALL 由 App 扩展发出 APP_LAUNCH，obox 创建或复用窗口并向目标扩展发 APP_OPEN_MSG；扩展以 APP_UI_MSG 回传 oml 或内联片段；single 为 true 时同应用最多一个窗口，persistent 为 true 时关闭仅隐藏、再开恢复状态，否则关闭即销毁并重新请求；single 为 false 时每次点击新建；三秒无回传显示提示。

#### Scenario: 持久化与多窗口
- **WHEN** 单窗口持久化应用关闭后重开，或非单窗口应用连点两次
- **THEN** 前者恢复原窗口与状态，后者出现两个窗口

### Requirement: i18n 注册与占位替换

扩展与 obox 主窗体 SHALL 能注册多语言文案：扩展的文案写在扩展目录的 i18n.json（数组，条目为 id、lang、value；id 以小写字母开头、可含数字与点），obox 自身同样用 i18n.json；注册参数为 name（扩展标识 名称.作者，主窗体为 obox）、id 与 values（BCP-47 到文案的字典，必须含 zh-CN）；视图片段中的 i18n 引用（双花括号包住 i18n 与条目 id） SHALL 在渲染前替换为当前语言文案，缺当前语言时回退 zh-CN，未注册的引用原样保留。obox SHALL 在标题栏提供语言切换入口，切换后自动重建全部视图与外壳文案，并把选择写入配置。

#### Scenario: 注册并替换
- **WHEN** 扩展注册 id 为 title、values 含 zh-CN 与 en-US，oml 里写 i18n.title 占位符
- **THEN** 当前语言为 zh-CN 时渲染中文，切到 en-US 时渲染英文

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

### Requirement: 控件过渡动画

组件 SHALL 在状态切换时带短促过渡：开关滑块滑动、复选框打勾淡入、单选圆点放大、按钮悬停与按下的底色过渡、提醒条与通知淡入、模态浮层淡入；过渡时长 90 到 220 毫秒，不阻塞消息处理。

#### Scenario: 开关切换
- **WHEN** 点击开关
- **THEN** 滑块在 170 毫秒内滑到另一端，轨道颜色同步过渡

#### Scenario: 按钮悬停
- **WHEN** 鼠标移入或移出按钮
- **THEN** 底色在 140 毫秒内过渡到悬停色或退回原色，按下时再压暗一点

#### Scenario: 浮层出现
- **WHEN** 提醒条、通知或模态被设为可见
- **THEN** 以淡入方式出现，不闪一下

### Requirement: 不依赖第三方控件库

工程 SHALL 只依赖 PySide6：按钮、输入、选择、滑块、表格、页签、开关、复选框、单选、标签、通知与浮层全部由纯 Qt 控件或自绘图元实现，依赖清单中不出现第三方组件库，代码中不出现其导入。

#### Scenario: 依赖清单

- **WHEN** 查看 pyproject 的 dependencies
- **THEN** 只有 PySide6

#### Scenario: 外观不回退

- **WHEN** 以 light 与 dark 打开组件画廊
- **THEN** 各类控件外观与替换前一致或更贴近主题

### Requirement: 扩展目录与清单

obox SHALL 扫描四个扩展根：安装目录的 extensions（系统扩展）、数据目录的 extensions（用户安装）、源码 extensions（开发）、命令行与配置指定的开发目录（dev）；同名扩展按「用户安装 > 系统 > 源码 > dev」优先并记录覆盖日志；dev 与已安装同 id 时本次会话以 dev 实现运行并在列表标记 origin=dev；目录需含合法 extension.json，入口为 extension.py 或 extension.pyd，.oix 先解压再扫描。安装 oix 时 SHALL 按文件名中的 -win-x64 / -win-arm64 与当前进程架构比对，不匹配直接拒绝。

#### Scenario: 合法源码扩展被识别

- **WHEN** extensions 下存在包含 extension.json 与 extension.py 的目录，且清单字段完整
- **THEN** obox 在扩展列表中列出该扩展，显示清单里的名称、版本、作者、描述与图标

#### Scenario: 合法安装扩展被识别

- **WHEN** .obox/extensions 下存在解压后的目录，含 extension.json 与 extension.pyd
- **THEN** obox 同样列出并激活该扩展

#### Scenario: 清单非法被拒绝

- **WHEN** extension.json 缺少名称或作者，或图标路径指向 assets 之外
- **THEN** obox 跳过该目录，并在日志中指明缺失字段与目录路径

### Requirement: 开发扩展加载

obox SHALL 支持 --dev-extension（可重复）与 DEV_EXTENSION_ADD/REMOVE 消息加载开发目录；目录需含合法 extension.json。开发目录 SHALL 只挂到扩展宿主，不复制到安装目录、不写 disabled 配置；路径列表写入配置 dev_extensions，下次启动自动加载；移除后列表与配置都不残留。

#### Scenario: 启动时加载开发目录
- **WHEN** 执行 obox --dev-extension D:\work\hello
- **THEN** 扩展列表出现 hello 且 origin 为 dev，安装目录不产生副本

#### Scenario: 运行中移除
- **WHEN** 发送 DEV_EXTENSION_REMOVE_MSG（payload 含 path）
- **THEN** 该扩展停用、配置删除、其它扩展不受影响

### Requirement: 断点调试

obox SHALL 支持 --debug 与 --debug-port，扩展宿主以 debugpy 在 127.0.0.1:端口 监听并等待 attach；--no-debug-wait 可跳过等待。debugpy SHALL 属于开发依赖，不进入发布包。仓库 SHALL 提供 .vscode/launch.json，包含 attach 扩展宿主与启动 obox 的配置。

#### Scenario: VS Code 命中断点
- **WHEN** obox 以 --debug 启动，VS Code attach 到端口并在开发目录 extension.py 设断点
- **THEN** 断点命中，可单步与查看变量

### Requirement: 开发目录热重载

obox SHALL 监听开发目录内文件变化，变化后自动重启扩展宿主并重新激活；--no-dev-reload 可关闭。

#### Scenario: 保存即生效
- **WHEN** 修改开发目录里的 extension.py 并保存
- **THEN** 宿主重启，开发扩展重新激活

### Requirement: 扩展命名空间 API

obox SHALL 向扩展提供按 VS Code 风格组织的命名空间 API：window、workspace、commands、env、extensions、storage、network、message、log；所有函数以只读 OboxContext 为第一个参数，函数与参数使用 camelCase。window SHALL 提供消息框、quickPick、inputBox、打开/保存对话框、模态 showMessageBox、createWindow/closeWindow/setWindowTitle/getActiveWindow/listWindows/focusWindow、状态栏、进度、输出通道与主题；network SHALL 提供 HTTP、TCP、UDP、QUIC、SSH、SFTP、ICMP 与统一代理；storage SHALL 提供 globalState/workspaceState；扩展不得直接依赖 Qt。

#### Scenario: 模态框只阻塞发起窗口
- **WHEN** 扩展在子窗口调用 showMessageBox
- **THEN** 子窗口不可交互，主窗口与其它子窗口仍可操作

#### Scenario: 新窗口
- **WHEN** 扩展调用 createWindow 传入 title 与 oml
- **THEN** 新窗口打开并渲染该 OML，返回 windowId

#### Scenario: 网络代理
- **WHEN** 设置页启用代理且扩展调用 network.request 未传 noProxy
- **THEN** 请求经代理发出；noProxy=True 时直连

#### Scenario: 上下文不可变
- **WHEN** 扩展给 ctx.extensionId 赋值
- **THEN** 抛出只读异常，订阅只能通过 ctx.subscriptions.add 添加

### Requirement: 扩展生命周期与上下文注入

扩展宿主 SHALL 在激活时调用 extension.py 的 activate 并注入 context，在停用时调用 deactivate；context 提供扩展标识、资产目录、存储目录、消息收发与注册点能力。

#### Scenario: 激活时拿到可用 context

- **WHEN** 扩展被激活
- **THEN** activate 收到的 context 能读到扩展名与作者、能访问 assets 与独立的存储目录、能注册命令

#### Scenario: 停用后能力失效

- **WHEN** 扩展被停用
- **THEN** deactivate 被调用一次，其注册的命令与视图不再可调用，未释放的订阅被回收

### Requirement: HTML 组件声明与装配

obox SHALL 把扩展提供的 HTML 片段解析为组件树，PascalCase 标签映射到套件实现的组件，并在扩展视图容器内装配成原生控件。

#### Scenario: 片段渲染为原生界面

- **WHEN** 扩展声明一个包含容器、按钮与输入框的片段
- **THEN** obox 在对应容器内渲染出对应的原生控件，层级与片段一致

#### Scenario: 未知标签被拒绝

- **WHEN** 片段中出现未注册的标签名
- **THEN** obox 拒绝整份片段，错误信息包含标签名与所在行列，容器保持原样

### Requirement: 组件标识唯一性

组件 SHALL 以 id 标识；扩展创建的组件在该扩展命名空间内唯一，obox 创建的组件在 obox 命名空间内唯一；重复 id 的创建请求被拒绝且不影响已存在的组件。

#### Scenario: 同扩展内重复 id

- **WHEN** 一个扩展第二次创建已经用过的 id
- **THEN** 创建失败并返回冲突错误，原有组件保持不变

#### Scenario: 跨扩展同名 id 互不影响

- **WHEN** 两个扩展各自创建 id 为 submit 的按钮
- **THEN** 两个组件都正常显示，事件分别只到达各自所属的扩展

### Requirement: 组件事件上报

obox SHALL 只在 HTML 片段用 on_ 前缀属性声明了回调时才投递组件事件；未声明的事件在装配阶段就不绑定回调，交互不会产生任何消息。

#### Scenario: 声明后点击才投递

- **WHEN** 片段的按钮带 on_click 属性，用户点击它
- **THEN** 该扩展收到 ComponentEventMessage，载荷仍是组件 id 与事件名

#### Scenario: obox 自身组件不外发

- **WHEN** 用户点击 obox 自己创建的组件
- **THEN** 不向任何扩展投递组件事件

### Requirement: 组件状态查询

扩展 SHALL 能发送 ComponentStateMessage 查询指定组件的状态，obox 以同一消息类型加返程标识回传状态值。

#### Scenario: 查回输入框的值

- **WHEN** 扩展查询某个输入框的 value 状态
- **THEN** obox 返回一条 reply 为真的 ComponentStateMessage，value 字段为该输入框的当前文本

#### Scenario: 查询不存在的组件

- **WHEN** 扩展查询一个从未创建过的 id
- **THEN** 请求以组件不存在错误结束，扩展进程不崩溃

### Requirement: 组件状态修改

扩展 SHALL 能发送 ComponentModifyMessage 修改自己创建的组件状态，obox 应用后返回确认；修改他人组件被拒绝。

#### Scenario: 修改输入框的 value

- **WHEN** 扩展对自己创建的输入框发送 value 的修改消息
- **THEN** 输入框显示新值，扩展收到应用成功的应答

#### Scenario: 越权修改被拒绝

- **WHEN** 一个扩展试图修改另一个扩展创建的组件
- **THEN** obox 拒绝该修改并返回越权错误，目标组件保持不变

### Requirement: 消息基类与广播语义

所有消息 SHALL 携带 src、dst 与 msg_id，并可标记载荷是否为返程；dst 为空表示广播，广播投递给全部已激活的扩展，且不接受返程。

#### Scenario: 广播送达所有扩展

- **WHEN** 任一方发送 dst 为空的普通消息
- **THEN** 所有已激活的扩展都收到该消息

#### Scenario: 广播不接受返程

- **WHEN** 有人对一条广播消息发起应答
- **THEN** 消息层拒绝该应答，发送方收到明确错误

### Requirement: 请求应答与异步等待

消息层 SHALL 为需要应答的请求建立关联，发送方可选择带超时的阻塞等待、回调或 await 获取结果；超时后请求以超时错误结束并清理关联。

#### Scenario: await 取回状态

- **WHEN** 扩展以协程方式发送状态查询并 await 结果
- **THEN** 应答到达后协程恢复并得到状态值，宿主的事件循环不被阻塞

#### Scenario: 超时释放关联

- **WHEN** 对端在超时时间内没有应答
- **THEN** 等待方收到超时错误，关联表不再保留该请求

### Requirement: 进程间通道

obox 与扩展宿主 SHALL 通过本地命名管道通信，帧为长度前缀加 UTF-8 JSON；不得监听任何 TCP 或 UDP 端口；宿主断开后能重连恢复。

#### Scenario: 启动建立通道

- **WHEN** obox 启动扩展宿主
- **THEN** 宿主连上命名管道并完成握手，之后的组件消息可以双向收发

#### Scenario: 宿主崩溃后恢复

- **WHEN** 扩展宿主进程异常退出
- **THEN** obox 在界面上提示并重启宿主，恢复后重新激活扩展

### Requirement: QSS 样式作用域

obox SHALL 提供全局主题 QSS；扩展可在 assets 中提供 QSS，只允许命中自己创建的组件，越界选择器被拒绝并记录。

#### Scenario: 扩展样式生效且不越界

- **WHEN** 扩展加载只以自己的组件 id 为选择器的 QSS
- **THEN** 该扩展的组件按样式渲染，其他扩展与 obox 界面的外观不变

#### Scenario: 越界选择器被拒

- **WHEN** 扩展的 QSS 里出现作用于全局或其他扩展组件的选择器
- **THEN** obox 拒绝整条规则并记录原因

### Requirement: 注册点

extension.json 的 contributes SHALL 支持 commands、views、viewsContainers、configuration 与 app 五类注册点；视图容器只能是 sidebar 或 bottom；obox 在激活时登记它们，并能按 id 调用命令、显示视图。

#### Scenario: 声明的命令可调用

- **WHEN** 扩展在清单声明命令并在 context 中注册处理函数
- **THEN** obox 的命令注册表出现该命令，调用时处理函数被执行

#### Scenario: 声明的视图可显示

- **WHEN** 扩展声明视图并指定 sidebar 或 bottom 容器
- **THEN** obox 在对应容器中创建该视图的入口，点击后显示由扩展片段装配的界面；写 main 时校验失败

### Requirement: 主界面三段布局

obox 主界面由上、中、下三段组成：顶栏左侧显示 obox 图标与名称、右侧提供窗口按钮；中部左侧为只显示图标的活动栏，右侧为侧栏视图区（容器名 sidebar）；底部为扩展注册区（容器名 bottom），没有扩展注册时不占空间；不存在 main 容器。

#### Scenario: 扩展注册到侧栏

- **WHEN** 扩展在清单中声明一个侧栏视图并带 svg 图标
- **THEN** 侧栏出现该扩展的图标，点击后内容区显示该扩展的视图

#### Scenario: 顶栏窗口按钮

- **WHEN** 用户点击顶栏右侧的最小化、最大化或关闭按钮
- **THEN** 窗口执行对应动作，关闭时退出主程序并回收扩展宿主

#### Scenario: 扩展注册到底部栏

- **WHEN** 扩展在清单中声明底部栏视图
- **THEN** 底部栏显示该扩展提供的组件；没有扩展注册时底部栏隐藏

### Requirement: 界面套件清单与加载

obox SHALL 从安装目录 themes/（源码态回退 .theme）与数据目录 themes/ 两处扫描主题，读取每个子目录的 theme.json（name、version、mode、entry）与 pyd，同名以数据目录优先并去重，形成可用套件清单；启动时按清单与 .obox/config.json 的 theme 字段选择一套，配置缺失时取 light，命令行参数可以临时覆盖；缺清单、缺 pyd 或版本不兼容时报错退出。

#### Scenario: 启动时枚举可用套件

- **WHEN** .theme 下同时存在 light 与 dark 两个子目录，且各自有 theme.json 与 pyd
- **THEN** obox 得到包含两者的可用套件清单，并按配置或默认值选中 light

#### Scenario: 缺失即失败

- **WHEN** .theme/light 下没有 pyd 文件
- **THEN** 启动失败并给出指明缺失路径的错误，不进入主窗口

### Requirement: 界面提供者契约

套件 SHALL 通过清单声明的入口工厂返回 provider，暴露标签到组件类的映射、套件元信息（名称、模式、版本）与主题 QSS；组件类通过声明式能力表与 obox 对接，且不依赖 obox 的任何模块。

#### Scenario: 工厂可用

- **WHEN** 加载某个套件的 pyd 并调用清单声明的入口函数
- **THEN** 得到包含 21 个标签的映射，标签小写后与既有取值一致

#### Scenario: 主题可取

- **WHEN** 询问 provider 的主题 QSS
- **THEN** 返回同时覆盖外壳与组件的样式文本，应用后外观生效

### Requirement: 组件能力接口与消息处理分界

套件组件 SHALL 声明 supported_states 与 state_accessors（状态名到读取与写入方法名的映射）、supported_events 与 event_methods（事件名到注册方法名的映射），并通过类型化方法（如 text 与 set_text）实现读写；obox SHALL 保留消息构造、注册表、路由、越权判断与应答，通过映射调用套件方法。

#### Scenario: 状态查询经映射

- **WHEN** 扩展查询某输入框的 value，且该组件把 value 映射到读取方法 text
- **THEN** obox 调用 text 得到当前文本并以应答回传，套件内部方法命名不受 obox 约束

#### Scenario: 不支持的状态被拒绝

- **WHEN** 扩展查询组件的 supported_states 之外的状态
- **THEN** obox 返回明确的不支持错误，不调用套件

### Requirement: 组件契约不变

两套套件 SHALL 提供与既有实现一致的标签名、状态名与事件名，扩展片段无需改动即可在任意一套下渲染。

#### Scenario: 同一片段在两套套件下都渲染

- **WHEN** 用 demo 扩展的片段分别在 light 与 dark 下装配
- **THEN** 两次都成功，组件 id 与标签一致

### Requirement: 视觉统一

每套套件 SHALL 提供统一主题：层级用背景色差、字号与留白建立；输入类控件默认带 1px 淡边框，其它控件默认不描边；控件圆角 10 到 12、卡片与浮层 16 到 20；不使用阴影；切换套件后外壳与内容区同时变化。

#### Scenario: 圆角与边框

- **WHEN** 渲染任意一套套件的输入框、卡片与表格
- **THEN** 三者默认没有可见边框，分隔靠底色差与留白；圆角取自套件常量

#### Scenario: 切换后整体变化

- **WHEN** 从 light 切到 dark
- **THEN** 顶栏、侧栏、底部栏与内容区一起变为深色

### Requirement: 运行中切换套件

obox SHALL 支持运行中切换套件：销毁现有视图并按新套件重建；新套件加载失败时保留原套件并报错。

#### Scenario: 切换失败回滚

- **WHEN** 请求切到不存在或损坏的套件
- **THEN** 保留当前套件的视图并给出错误提示，进程不退出

### Requirement: 构建与 pyd 产物

工程 SHALL 提供 x86_64 与 ARM64 两种目标的构建：把 theme/{name} 编译为 themes/{name}/{name}.pyd 并复制 theme.json、styles.qss 与字体，把系统扩展（app、settings、management）编译为 extensions/{id}/extension.pyd 目录；安装包 SHALL 包含这两类目录；用户扩展的 oix SHALL 按架构分别产出。构建失败以非零退出码结束且不留半成品。

#### Scenario: 构建产物齐全

- **WHEN** 执行构建命令
- **THEN** .theme/light 下同时出现 light.pyd 与 theme.json

### Requirement: 测试链路

测试 SHALL 以内存假 provider 为主，另有一条加载真实 pyd 的集成用例验证工厂、清单与标签映射。

#### Scenario: 假 provider 跑常规用例

- **WHEN** 执行常规测试且未构建任何 pyd
- **THEN** 用例通过，装配与外观通过注入的 provider 验证

### Requirement: 主题色板与文字层级

两套套件 SHALL 各自提供低饱和色板：背景、表面、次级文字、分割线与强调色，强调色饱和度明显低于高饱和蓝，大面积背景不出现纯黑与纯白；文字层级只用字号与文字色阶区分。

#### Scenario: light 色板为暖白低饱和

- **WHEN** 以 light 套件渲染主界面
- **THEN** 背景是暖白、正文是中深灰、辅助文字更浅，强调色低饱和且不与背景形成刺眼对比

#### Scenario: dark 色板为深中性灰

- **WHEN** 以 dark 套件渲染主界面
- **THEN** 背景是深中性灰而不是纯黑，强调色在同一色相上降饱和

### Requirement: 间距与密度参数

套件 SHALL 暴露间距参数（视图边距、组件间距、控件高度），装配器与组件按参数取值，不写死固定像素值。

#### Scenario: 间距由套件驱动

- **WHEN** 装配一个扩展视图
- **THEN** 视图边距 20、组件间距 16，切换套件后间距随套件变化

#### Scenario: 控件高度

- **WHEN** 渲染按钮、输入框与下拉框
- **THEN** 高度为 38，与留白参数匹配

### Requirement: 选择容器与卡片

选择容器 SHALL 支持 mode 为 single 或 multiple，内部放若干卡片；卡片用 value 标识，内部可放任意自定义组件；被选中的卡片背景变色并在右下角显示对勾；容器暴露 value（选中 value 的列表）并投递 change 事件；单选允许再次点击清空。卡片 SHALL 也可独立使用：不放进选择容器时按普通容器展示自定义内容，声明 on_click 后点击投递 click 事件，悬停时描边变强调色。

#### Scenario: 独立使用卡片

- **WHEN** 片段写一个不在 Choice 内的 Card，内含若干组件并声明 on_click
- **THEN** 卡片按普通容器展示内容，点击时投递 click 事件，悬停时描边变色

#### Scenario: 多选切换

- **WHEN** 容器 mode 为 multiple，依次点击两张卡片
- **THEN** 两张都被选中，value 返回两个 value，且每次点击都投递 change 事件

#### Scenario: 单选互斥与清空

- **WHEN** 容器 mode 为 single，点击另一张卡片，再点同一张
- **THEN** 选中项先切换到新卡片，再次点击后清空

### Requirement: 提醒条组件

组件库 SHALL 提供提醒组件：type 取 info、warn、error，分别使用半透明浅蓝、浅黄、浅红底色与白色文字，左侧图标、右侧文本；position 取 top 或 bottom，offset 指定与窗体上下边缘的距离（px）；显隐由 visible 状态控制，默认隐藏。

#### Scenario: 三种类型

- **WHEN** 片段分别写 type 为 info、warn、error
- **THEN** 依次渲染浅蓝、浅黄、浅红半透明底，文字为白色，左侧带对应图标

#### Scenario: 顶部与底部定位

- **WHEN** position 为 top、offset 为 24，或 position 为 bottom、offset 为 40
- **THEN** 前者距窗口顶边 24px，后者距窗口底边 40px，宽度随窗口变化

### Requirement: 自绘标题栏

窗口 SHALL 使用无边框窗口与自绘标题栏：左侧显示应用图标（保持原色，不重染）与标题，右侧提供最小化、最大化/还原、关闭；支持拖动标题栏移动窗口、双击切换最大化、拖拽窗口边缘缩放、右键弹出系统菜单；Windows 上启用系统阴影与圆角。

#### Scenario: 标题栏显示与按钮

- **WHEN** 主窗口打开
- **THEN** 顶部显示自绘标题栏，含图标、标题与三个窗口按钮，不出现系统原生标题栏

#### Scenario: 拖动与双击

- **WHEN** 按住标题栏拖动，或双击标题栏
- **THEN** 窗口跟随移动；双击在最大化与还原之间切换，按钮提示同步变化

#### Scenario: 边缘缩放

- **WHEN** 把鼠标移到窗口四边或四角并拖动
- **THEN** 窗口按方向缩放，且不小于最小尺寸

### Requirement: 侧栏图标单色化与选中态

侧栏图标 SHALL 以单色渲染：套件给出未选中与选中的颜色，obox 把扩展提供的 svg 按 alpha 蒙版重染为单色；当前视图对应的图标用选中色，其余用弱色，切换视图时同步更新。

#### Scenario: 彩色 svg 显示为单色

- **WHEN** 扩展提供一张多色 svg 作为图标
- **THEN** 侧栏显示该图形轮廓的单色版本，而不是原始彩色

#### Scenario: 选中变色

- **WHEN** 点击某个扩展图标切到它的视图
- **THEN** 该图标变为套件的选中色，其它图标回到弱色

### Requirement: 边框可按需配置

组件 SHALL 支持 border 属性：all 表示四边都有、none 表示去掉、也可用逗号指定 top、right、bottom、left 的子集；输入类控件缺省为 all，其它组件缺省为 none；非法取值装配时报错。

#### Scenario: 默认完整边框

- **WHEN** 片段只写 Input 而不写 border
- **THEN** 输入框四边都有 1px 淡边框

#### Scenario: 关闭或只保留部分边

- **WHEN** 片段写 border 为 none，或 border 为 bottom
- **THEN** 前者没有边框，后者只保留底边

### Requirement: 套件自带字体

每套套件 SHALL 自带字体文件并在运行时注册，字体不依赖系统安装；切换套件时字体随之切换，字体缺失时回退到系统字体栈。

#### Scenario: 套件字体生效

- **WHEN** 以 light 套件启动
- **THEN** 界面文字使用套件 fonts 目录里的 HarmonyOS Sans SC，而不是系统回退字体

#### Scenario: 字体缺失回退

- **WHEN** 套件目录里没有字体文件
- **THEN** 使用 QSS 里的系统字体栈渲染，不报错退出

### Requirement: 弹性布局容器

套件 SHALL 提供 Flex 容器组件，支持 direction、wrap、justify、align、gap 与子项 grow；容器尺寸变化时按上述规则重新排布。

#### Scenario: 主轴对齐与间距

- **WHEN** 片段写 direction 为 row、justify 为 center、gap 为 12，放入三个按钮
- **THEN** 三个按钮水平居中，彼此间隔 12，容器变宽后仍居中

#### Scenario: 换行与伸缩

- **WHEN** wrap 为 wrap，或某个子项写 grow 为 1
- **THEN** 子项按行折行；写 grow 的子项吃掉主轴剩余空间

#### Scenario: 非法属性被拒绝

- **WHEN** justify 写成不存在的取值
- **THEN** 装配失败并指出属性与合法取值

### Requirement: 组件展示页

工程 SHALL 提供 extensions/gallery 扩展，在一页内展示全部 20 个内容组件与 Flex 布局样例，作为视觉验收与 antd 对照的依据。

#### Scenario: 展示页覆盖全部组件

- **WHEN** 打开 gallery 扩展的视图
- **THEN** 页面按分组展示 20 个内容组件，并有一块 Flex 布局示例

#### Scenario: 截图可对照 antd

- **WHEN** 对展示页截图
- **THEN** 按钮、输入框、选择器的高度与间距可量出与 antd 同量级，色板保持低饱和

### Requirement: 安装包构建

工程 SHALL 只提供一个安装包：scripts/build_installer.py 准备 obox.exe（Nuitka standalone）、.theme 与系统扩展，生成 .nsi 并调用 makensis，产出 dist 下的 setup 可执行文件；安装包提供范围页（所有用户 / 仅为我安装）与目录页，静默安装用 /ALLUSERS 或 /CURRENTUSER 指定范围、/D 指定目录，缺省所有用户；所有用户安装需管理员权限，当前用户安装不需要。

#### Scenario: 选择范围与目录
- **WHEN** 交互运行安装包
- **THEN** 先选所有用户或当前用户，再在目录页改安装路径，安装到所选位置

#### Scenario: 静默安装
- **WHEN** 运行安装包 /S /CURRENTUSER /D=某目录
- **THEN** 装到该目录并写 HKCU 注册表，无需管理员

#### Scenario: 卸载
- **WHEN** 运行安装目录下的卸载程序
- **THEN** 按安装时范围删除程序文件、快捷方式与对应注册表项，保留用户数据

### Requirement: 安装目录布局

安装目录 SHALL 为：obox.exe 与 Nuitka 运行时文件、.theme/{light,dark}、extensions/{app,settings}（已解压的系统扩展，不是 .oix）；不含源码。默认路径：所有用户为 Program Files 下的 obox，当前用户为 %LOCALAPPDATA%\\Programs\\obox，均可在目录页修改。

#### Scenario: 安装后结构
- **WHEN** 完成安装
- **THEN** 安装目录可直接启动，侧栏出现应用与设置两个系统扩展

### Requirement: 运行期路径解析

obox SHALL 区分程序目录与数据目录：安装态程序目录为 exe 所在目录、数据目录为 %LOCALAPPDATA%\\obox；源码态为仓库根与仓库根的 .obox。配置、扩展存储与用户安装的 .oix 都落在数据目录。

#### Scenario: 安装态写配置
- **WHEN** 安装版运行并切换语言
- **THEN** 配置写入 %LOCALAPPDATA%\\obox/config.json，程序目录不被修改

### Requirement: 扩展打包产物

工程 SHALL 提供一条命令，分析指定扩展目录内的 import 图，把入口与关联的本地 Python 文件各自编译为同名 pyd，与 extension.json、assets 一起打成 zip，产物为 dist/名称.作者.{版本}.oix。

#### Scenario: 打包一个合法扩展

- **WHEN** 对包含 extension.json 与 extension.py 的目录执行打包命令
- **THEN** dist 下出现 名称.作者.{版本}.oix，zip 根目录含 extension.json、extension.pyd、i18n.json（若有）与 assets/、views/

#### Scenario: 漏了清单

- **WHEN** 目标目录没有 extension.json
- **THEN** 命令以非零退出并指出缺少清单，不产出半成品

### Requirement: 扩展安装

obox SHALL 在 .obox/extensions 下发现 .oix 文件时，把它解压到同名目录 名称.作者；目录已存在时覆盖，并拒绝越出安装目录的压缩包成员。

#### Scenario: 安装 oix

- **WHEN** 把 gallery.obox.0.1.0.oix 放进 .obox/extensions
- **THEN** 解压出 gallery.obox 目录，含 extension.json、extension.pyd 与 assets/

#### Scenario: 拒绝路径穿越

- **WHEN** 压缩包成员指向安装目录之外
- **THEN** 该包安装失败并记录原因，安装目录内不出现越界文件

### Requirement: pyd 入口加载与模块搜索路径

obox SHALL 扫描 .obox/extensions 与 extensions/ 两个根，按清单识别扩展；入口存在 extension.pyd 时优先加载 pyd，否则回退 extension.py，并把扩展目录加入模块搜索路径以解析同包依赖。

#### Scenario: 从安装目录加载 pyd 扩展

- **WHEN** .obox/extensions/{id} 下有 extension.json 与 extension.pyd
- **THEN** 扩展被激活，视图与命令正常注册

#### Scenario: 加载时注入搜索路径

- **WHEN** 扩展的 pyd 运行时 import 同目录的其它模块
- **THEN** 能从扩展目录解析到该模块，不报找不到包

#### Scenario: 本地模块重名

- **WHEN** 两个扩展各自带同名本地模块
- **THEN** 先加载者生效，日志记录冲突告警，进程不退出

### Requirement: 扩展开发技能

工程 SHALL 提供 .agents/skills/obox-ext-dev：SKILL.md 说明触发与步骤；references 覆盖清单（含 contributes.app 与 configuration）、context API（含配置下发与 App 窗口数据通道）、oml、i18n、打包；templates 提供可拷贝的清单/入口/oml/i18n/图标；scripts 提供扩展脚手架与清单校验。

#### Scenario: 脚手架生成可运行扩展
- **WHEN** 运行 scaffold_extension.py 并给出名称与作者
- **THEN** 生成的目录可被 obox 激活，check_extension.py 通过

### Requirement: 主题开发技能

工程 SHALL 提供 .agents/skills/obox-theme-dev：references 覆盖组件契约、主题常量与构建；templates 提供组件与 theme.py 骨架；scripts 提供契约校验与组件脚手架。

#### Scenario: 契约校验
- **WHEN** 运行 check_theme.py
- **THEN** 输出两套套件的标签数与缺失项，通过时退出 0

### Requirement: 界面验证技能

工程 SHALL 提供 .agents/skills/obox-ui-test：references 覆盖 driver、verify 场景与常见坑；templates 提供场景片段；scripts 提供一键跑两套主题验证并汇总退出码与截图的脚本。

#### Scenario: 一键验证
- **WHEN** 运行 run_verify.py
- **THEN** 依次跑 light/dark，打印截图与退出码，任一失败整体非零

### Requirement: 测试检查技能

工程 SHALL 提供 .agents/skills/obox-test：references 覆盖测试矩阵、质量门禁与排障；templates 提供组件测试骨架；scripts 提供汇总 ruff、pytest 与各 US 基线校验的脚本。

#### Scenario: 汇总检查
- **WHEN** 运行 check_all.py
- **THEN** 依次执行静态检查、测试与基校验并汇总，失败时非零

### Requirement: 组件与接口变更同步技能

AGENTS.md SHALL 规定：任何组件标签/状态/事件/契约、theme 常量与 QSS、清单字段、context API、oml 指令、i18n.json、应用/配置贡献、打包产物、verify 场景或测试门禁发生变化时，必须在同一次改动中更新 .agents/skills 对应技能；提交前运行 check_all.py。

#### Scenario: 组件变化同步主题技能
- **WHEN** 新增或修改组件标签与契约
- **THEN** obox-theme-dev 的 references 与模板同步更新，标签计数保持一致

### Requirement: 技能目录约定

四个技能 SHALL 遵循统一结构：SKILL.md 带 name 与 description frontmatter，目录名与 name 一致；references/templates/scripts 按需存在；脚本在仓库根可直接运行，references 指向真实文件与命令。

#### Scenario: 目录可被发现
- **WHEN** 列出 .agents/skills
- **THEN** 出现四个技能目录，SKILL.md 的 name 与目录名一致

### Requirement: 单实例运行

obox SHALL 保证每个 Windows 用户最多一个运行实例：启动时以按用户命名的本地管道探测，已有实例则发送显示请求并退出，没有则成为主实例并监听管道。

#### Scenario: 第二次启动
- **WHEN** obox 已在运行，用户再次启动
- **THEN** 新进程退出，已运行实例的窗口显示并置前

### Requirement: 托盘常驻

obox SHALL 在系统托盘显示图标：双击恢复主窗口，右键菜单提供显示主窗口、打开设置、退出；托盘对象在最小化到托盘后仍存在，退出时移除。

#### Scenario: 托盘恢复
- **WHEN** 窗口已最小化到托盘，用户双击托盘图标
- **THEN** 主窗口恢复显示并置前

### Requirement: 关闭行为

关闭主窗口时 SHALL 按配置处理：询问时弹出三选一（最小化到托盘、退出、取消）并可勾选「记住我的选择」；直接最小化或直接退出时不询问；记住后写入配置。

#### Scenario: 记住选择
- **WHEN** 在对话框中勾选记住并选择最小化
- **THEN** 配置写入 close_action=tray，下次关闭不再询问

### Requirement: 关闭行为设置

设置页 SHALL 提供「行为」分类，关闭行为可选每次询问、最小化到托盘、直接退出，修改即时生效并持久化。

#### Scenario: 设置切换
- **WHEN** 把关闭行为改为直接退出
- **THEN** 关闭窗口直接退出，配置为 quit

### Requirement: 设置扩展

工程 SHALL 提供系统扩展 extensions/settings（name=settings、publisher=obox、version=1.0.0）：只注册 sidebar 视图；界面仿 VSCode，左侧分类（外观、语言、扩展、关于）、右侧设置项、顶部搜索；外观与语言修改即时生效。

#### Scenario: 分类与设置项
- **WHEN** 打开设置页
- **THEN** 左侧出现四个分类，右侧显示当前分类的设置项与说明

### Requirement: 扩展配置贡献

extension.json SHALL 支持 contributes.configuration：属性名只能是小写字母数字，属性表每项声明 type（bool、string、enum）、title、default 与可选 enum；obox 校验后汇总成设置项下发；非法类型、缺 title、enum 默认值不在枚举内都会被拒绝。obox SHALL 在扩展激活后与设置写入后，把该扩展的配置当前值以 EXTENSION_CONFIG_MSG（values + defaults，键为属性名）发给它。

#### Scenario: 贡献出现在设置页
- **WHEN** 扩展声明两个配置项
- **THEN** 设置页「扩展」分类出现对应控件，默认值来自 default

### Requirement: 远程桌面扩展

工程 SHALL 提供用户扩展 rdp.chenzhi：contributes.app 提供「远程桌面」卡片，界面含连接列表、搜索与新建/编辑模态框（折叠分组），连接字段覆盖账号、显示、连接、音频、本地资源与体验。打开连接时生成 .rdp，记住密码时写入 DPAPI 密文到 password 51:b 字段，并以脱离 obox 进程树的方式启动 mstsc；非 Windows 平台提示不支持。

#### Scenario: 新建并打开连接
- **WHEN** 填入名称、主机与账号后保存并点「连接」
- **THEN** 生成 .rdp 并启动独立 mstsc 进程，列表出现该连接

#### Scenario: 删除需确认
- **WHEN** 点某条连接的「删除」
- **THEN** 先弹出确认框，确认后才删除记录与密文

### Requirement: 网页应用扩展

工程 SHALL 提供用户扩展 webapp.chenzhi：contributes.app 提供「网页应用」卡片，站点字段含名称、URL、说明、忽略证书、额外 origin、窗口尺寸/位置、启动最大化、语言、缩放与禁用 GPU。打开时用 Chrome 的 app 模式与独立 profile 目录启动并脱离 obox；找不到 Chrome 或超出配置的数据上限时在页面提示。

#### Scenario: 打开站点
- **WHEN** 站点 URL 有效且本机有 Chrome
- **THEN** Chrome 以 --app 模式启动，profile 位于配置根下的条目目录

### Requirement: 运行时资源目录

宿主 SHALL 从安装目录 themes/ 与 extensions/、数据目录 themes/ 与 extensions/ 加载资源；同名以数据目录优先；安装目录缺失时仍可用用户目录启动。

#### Scenario: 系统主题预装
- **WHEN** 安装包安装后首次启动
- **THEN** 主题列表包含安装目录 themes 下的 light 与 dark

#### Scenario: 用户扩展与系统扩展并存
- **WHEN** 数据目录安装了 rdp，安装目录有 app/settings/management
- **THEN** 启动后四类扩展都可用

### Requirement: 仓库与发布流程

组织 SHALL 维护 obox（主程序、系统扩展、系统主题）、rdp、webapp 三个仓库；改动经分支与 Pull Request 合并，PR 上运行测试与打包冒烟；打 v 开头 tag 时构建 Release 产物，包含 x86_64 与 ARM64 安装包，以及用户扩展对应架构的 oix。

#### Scenario: tag 发布
- **WHEN** 打 v1.0.0
- **THEN** Release 附带 obox x86_64/arm64 安装包与 rdp、webapp 两种架构的 oix

### Requirement: 设置读写

设置扩展 SHALL 通过 SETTINGS_SET 提交修改；obox SHALL 把值写入 .obox/config.json 的 settings 段（键为 扩展标识.属性名），并对主题与语言立即应用；写入失败时保留旧值并回报错误。

#### Scenario: 立即生效
- **WHEN** 把语言改成 en-US
- **THEN** 界面切换为英文，配置里 settings.obox.language 为 en-US

### Requirement: 设置搜索

设置页 SHALL 提供搜索框：按分类名与设置项标题/描述做不区分大小写的子串过滤，空查询显示全部；过滤在设置扩展内完成并回注视图数据。

#### Scenario: 过滤与恢复
- **WHEN** 输入「主题」后清空
- **THEN** 先只显示外观分类，清空后恢复四个分类

### Requirement: 扩展故障隔离

单个扩展激活失败 SHALL 不阻断其他扩展激活；宿主进程异常退出后，obox 重启宿主并恢复扩展。

#### Scenario: 单个扩展抛出异常

- **WHEN** 某个扩展的 activate 抛出异常
- **THEN** 该扩展被标记为失败，其他扩展继续激活，界面提示失败原因