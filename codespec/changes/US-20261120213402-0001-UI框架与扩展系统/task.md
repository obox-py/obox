---
status: done
---

# Tasks

## 拆分方式

按模块加波次：任务边界落在 obox/api、obox/core、obox/ui、obox/extensions 四个子包上，同一文件不跨任务；依赖关系决定 9 个波次，同波次内文件不重叠，可派 subagent 并行。对应需求一列指向基线 spec.md 的 13 条需求与 delta 新增的「主界面三段布局」。

## 全局约束

- 不引入 Web 引擎：除 PySide6 与 PySide6-Fluent-Widgets 外不新增第三方依赖，禁止添加 QtWebEngine。
- obox/api 不 import 任何 PySide6 界面模块，保持纯 Python 契约层，两个进程都能导入。
- 消息的 src 与 dst 只允许 obox 或 名称.作者 两种格式；组件消息的 msg_id 固定，禁止扩展派生新类型。
- 组件必须先经注册表登记才能上屏，禁止绕过注册表直接实例化后挂到视图。
- 所有跨进程通道只使用命名管道，不得监听任何 TCP 或 UDP 端口。

## 任务清单

| ID | 任务 | 方式 | 涉及文件 / 模块 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 工程骨架与依赖声明 | 主 Agent | `pyproject.toml`、`obox/__init__.py`、`obox/main.py`、`obox/assets/obox.svg` | 扩展目录与清单 | - | `python -m obox.main --version` 输出 obox 1.0.0，根 main.py 已删除 | 完成 |
| T2 | 安装依赖并验证导入 | 后台 | `pip install -e .` | 进程间通道 | T1 | 退出码 0，且能打印 PySide6 与 qfluentwidgets 版本 | 完成 |
| T3 | 消息基类与序列化 | subagent | `obox/api/message.py`、`tests/test_message.py` | 消息基类与广播语义 | T1 | `python -m pytest tests/test_message.py -q` 全绿 | 完成 |
| T4 | 组件消息三件套与枚举 | subagent | `obox/api/component.py`、`obox/api/events.py`、`obox/api/states.py`、`obox/api/errors.py`、`tests/test_component.py` | 组件事件上报、组件状态查询、组件状态修改 | T3 | 三件套 msg_id 固定、派生抛 TypeError、方向校验通过 | 完成 |
| T5 | 请求对象与三种等待形态 | subagent | `obox/api/request.py`、`tests/test_request.py` | 请求应答与异步等待 | T3 | 阻塞、回调、await 与超时四条用例全绿 | 完成 |
| T6 | 帧编解码 | subagent | `obox/core/ipc/framing.py`、`tests/test_framing.py` | 进程间通道 | T3 | 半包、粘包、超长帧用例全绿 | 完成 |
| T7 | 命名管道服务端与客户端 | subagent | `obox/core/ipc/server.py`、`obox/core/ipc/client.py`、`tests/test_ipc.py` | 进程间通道 | T6 | 本机回环收发一帧成功，握手失败被拒 | 完成 |
| T8 | 消息总线 | subagent | `obox/core/bus.py`、`tests/test_bus.py` | 消息基类与广播语义、请求应答与异步等待 | T4、T5 | 路由、广播、关联应答、超时与广播应答拒绝用例全绿 | 完成 |
| T9 | 组件解析器 | subagent | `obox/ui/parser.py`、`tests/test_parser.py` | HTML 组件声明与装配 | T2 | 嵌套、自闭合、未知标签带行列用例全绿 | 完成 |
| T10 | 组件注册表 | subagent | `obox/ui/registry.py`、`tests/test_registry.py` | 组件标识唯一性 | T9 | 重复 id 拒绝、跨命名空间隔离、注销清理用例全绿 | 完成 |
| T11 | 组件基类与 15 个组件 | subagent | `obox/ui/components/` | HTML 组件声明与装配、组件事件上报、组件状态查询、组件状态修改 | T10、T4 | 15 个组件各自可读写状态，Button 点击发出事件 | 完成 |
| T12 | 装配器 | subagent | `obox/ui/builder.py`、`tests/test_builder.py` | HTML 组件声明与装配、组件标识唯一性 | T11、T9、T10 | 片段装配出正确控件层级，id 冲突时整片回滚 | 完成 |
| T13 | QSS 过滤与主题 | subagent | `obox/ui/qss.py`、`obox/ui/theme.py`、`tests/test_qss.py` | QSS 样式作用域 | T10 | 合法规则生效、越界规则被拒并留原因 | 完成 |
| T14 | 扩展清单与目录扫描 | subagent | `obox/extensions/manifest.py`、`obox/extensions/loader.py`、`tests/test_manifest.py` | 扩展目录与清单 | T2 | 合法清单通过、缺字段与路径穿越被拒 | 完成 |
| T15 | 扩展 context 与注册点 | subagent | `obox/extensions/context.py`、`obox/extensions/contributions.py`、`tests/test_context.py` | 扩展生命周期与上下文注入、注册点 | T4、T5、T14 | 命令可注册可调用、视图可登记、注销后失效 | 完成 |
| T16 | 扩展宿主进程 | subagent | `obox/extensions/host.py`、`tests/test_host.py` | 进程间通道、扩展生命周期与上下文注入、扩展故障隔离 | T7、T15 | 握手后激活扩展，单个扩展抛异常不影响其他扩展 | 完成 |
| T17 | 宿主进程管理 | subagent | `obox/extensions/supervisor.py`、`tests/test_supervisor.py` | 扩展故障隔离、进程间通道 | T7、T16 | 子进程退出后 5 秒内重启并重新握手 | 完成 |
| T18 | 主窗口与应用装配 | 主 Agent | `obox/ui/main_window.py`、`obox/app.py`、`obox/main.py`、`tests/test_app_smoke.py` | 注册点、扩展生命周期与上下文注入 | T8、T12、T13、T17 | `python -m pytest tests/test_app_smoke.py -q` 全绿 | 完成 |
| T19 | 示范扩展 | subagent | `extensions/demo/` | 注册点、扩展目录与清单 | T15 | 清单校验通过，视图片段可装配，命令可调用 | 完成 |
| T20 | 端到端联调 | 主 Agent | `tests/test_e2e.py`、`scripts/verify_ui.py`、全量代码 | 组件事件上报、组件状态修改、扩展故障隔离 | T18、T19、T22 | 点击按钮后扩展收到事件并回改状态；杀宿主后自动恢复 | 完成 |
| T21 | 文档与基线回填 | 主 Agent | `README.md`、`docs/arch.md` | 扩展目录与清单 | T20 | 基线校验脚本全绿，目录树与实测性能与实现一致 | 完成 |
| T23 | 主界面三段式外壳 | 主 Agent | `obox/ui/main_window.py`、`obox/app.py`、`obox/extensions/host.py` | 主界面三段布局 | T18 | 启动后顶栏显示图标与标题、侧栏按扩展图标排列、底部栏在无注册时隐藏 | 完成 |
| T22 | UI 自动化验证脚本 | 主 Agent | `scripts/` | 组件事件上报、组件状态修改、HTML 组件声明与装配 | T18、T19 | `python scripts/verify_ui.py` 跑通全部场景，截图落 tmp/pics，日志落 tmp/logs | 完成 |
| T24 | theme/light 组件库 | subagent | `theme/light/` | 组件契约不变、视觉统一 | T26 | 15 个组件的标签、状态映射与具名事件方法齐全，可直接导入并读写 | 完成 |
| T25 | theme/dark 组件库 | subagent | `theme/dark/` | 组件契约不变、视觉统一 | T26 | 与 light 同构的 15 个组件与深色主题，标签与状态契约一致 | 完成 |
| T26 | 组件协议与校验 | 主 Agent | `obox/ui/component_protocol.py` | 界面提供者契约、组件能力接口与消息处理分界 | - | 协议校验能拒绝缺映射或缺具名方法的组件类 | 完成 |
| T27 | kit 加载器与套件扫描 | subagent | `obox/ui/kit.py` | 界面套件清单与加载、界面提供者契约 | T26 | 扫描能列出 .theme 下全部套件；缺清单、版本不符、pyd 不存在三种错误都有明确信息 | 完成 |
| T28 | 装配器与声明式事件 | subagent | `obox/ui/builder.py`、`obox/ui/parser.py` | 组件事件上报、组件能力接口与消息处理分界 | T24、T26 | 片段写了 on_click 才绑定回调，没写不产生消息；状态经映射读写 | 完成 |
| T29 | 启动选库与运行中切换 | 主 Agent | `obox/app.py`、`obox/main.py`、`.obox/config.json` | 界面套件清单与加载、运行中切换 kit | T27、T28 | 缺省加载 light；切 dark 成功重建；dark 损坏时回滚并提示 | 完成 |
| T30 | Nuitka 构建脚本 | 主 Agent | `scripts/build_theme.py` | 构建与 pyd 产物 | T24、T25 | 一条命令产出两套 pyd 与清单；失败非零退出且不留半成品 | 完成 |
| T31 | 测试改造与 pyd 集成 | subagent | `tests/` | 测试链路 | T28、T30 | 常规用例不依赖构建即可通过；集成用例加载真实 pyd 断言 15 标签 | 完成 |
| T32 | 视觉验收与文档 | 主 Agent | `README.md`、`tmp/pics/` | 视觉统一、构建与 pyd 产物 | T29、T30 | light 与 dark 各一张截图；README 有构建、选择与切换说明 | 完成 |
| T34 | 组件替换为纯 Qt | 主 Agent | `theme/*/components/*.py`、`theme/*/theme.py` | 不依赖第三方控件库 | T3 | 12 个组件不再导入控件库，light/dark 画廊外观正常 | 完成 |
| T35 | 移除依赖与主窗口收尾 | 主 Agent | `obox/app.py`、`obox/ui/main_window.py`、`pyproject.toml` | 不依赖第三方控件库 | T34 | pyproject 只剩 PySide6；全仓 0 处 qfluentwidgets；测试全过 | 完成 |
| T37 | 按钮悬停与按下过渡 | 主 Agent | `theme/*/components/button.py`、`modal.py`、`tests/test_button_animation.py` | 控件过渡动画 | T36 | 按钮自绘并带 hover/press 过渡；悬停 220ms 后 hover 到 1.0 | 完成 |
| T36 | 控件过渡动画 | 主 Agent | `theme/*/components/{switch,checkbox,radio,alert,notification,modal}.py`、`tests/test_animation.py` | 控件过渡动画 | T34 | 开关/复选/单选属性随时间变化；浮层淡入；2 例动画测试通过 | 完成 |
| T38 | i18n 注册与替换 | 主 Agent | `obox/i18n.py`、`obox/api/i18n.py`、`obox/extensions/context.py`、`obox/app.py` | i18n 注册与占位替换 | T3 | 注册后 oml 占位符按语言替换；缺 zh-CN 被拒；10 例测试通过 | 完成 |
| T39 | 视图文件格式 | 主 Agent | `obox/oml.py`、`obox/app.py`、`extensions/{demo,gallery}/views/`、`tests/test_oml.py` | 视图文件格式 | T38 | demo/gallery 从 oml 渲染；越界与缺失被拒；verify 断言 i18n 文案 | 完成 |
| T40 | 语言手动切换 | 主 Agent | `obox/ui/title_bar.py`、`obox/ui/main_window.py`、`obox/app.py`、`scripts/verify_ui.py` | i18n 注册与占位替换 | T38 | 标题栏菜单可切中英；切换后视图与首页文案重建；verify 断言英文标题 | 完成 |
| T41 | i18n.json 与视图打包 | 主 Agent | `scripts/pack_extension.py`、`tests/test_pack_i18n.py` | 视图文件格式 | T39 | oix 内含 i18n.json 与 views/；安装后从 pyd 加载仍能渲染 | 完成 |
| T33 | 删除旧组件包并迁移 demo | 主 Agent | `obox/ui/components/`、`extensions/demo/`、`tests/` | 组件契约不变、组件事件上报 | T28、T31 | 旧组件包删除；demo 片段补 on_click 且点击仍能往返；回归全绿 | 完成 |

## 任务详情

### T1 工程骨架与依赖声明

- 步骤：
  1. pyproject.toml 补 dependencies（PySide6、PySide6-Fluent-Widgets）、[project.scripts] obox = obox.main:main、[tool.pytest.ini_options] testpaths
  2. 建 obox/api、obox/core/ipc、obox/ui/components、obox/extensions、obox/assets 与 tests，各带 __init__.py
  3. 把 tmp/obox.svg 迁到 obox/assets/obox.svg，删除仓库根的 main.py
  4. obox/__init__.py 写 __version__；obox/main.py 先只实现 --version
- 验收命令：`python -m obox.main --version`（期望：输出 obox 1.0.0，退出码 0）
- 自检：目录树与 delta-design 的 Changes 一致；tmp 下不再有 obox.svg；根 main.py 已删除

### T2 安装依赖并验证导入

- 步骤：
  1. 在虚拟环境内执行 pip install -e .
  2. 验证 import PySide6、import qfluentwidgets，打印两者版本
  3. 记录装不上的版本与替代方案到交付说明
- 验收命令：`pip install -e . && python -c "import PySide6, qfluentwidgets; print(PySide6.__version__)"`（期望：退出码 0 并打印版本）
- 自检：确认没有同时安装 PyQt 系的 Fluent-Widgets 包（会与 qfluentwidgets 冲突）

### T3 消息基类与序列化

- 步骤：
  1. 定义 Message（src、dst、msg_id、reply、correlation_id、payload）与三个组件消息常量
  2. 实现 to_dict 与 from_dict，from_dict 校验必填字段与 src/dst 格式
  3. 测试覆盖往返、缺字段、广播判定（dst 为空）
- 验收命令：`python -m pytest tests/test_message.py -q`（期望：全部通过）
- 自检：广播判定与 src 格式校验都有反例

### T4 组件消息三件套与枚举

- 步骤：
  1. 三个子类固定 MSG_ID，用 __init_subclass__ 拒绝派生
  2. events.py 定义事件名常量（click、dblclick、contextmenu、input、change、checkedchange、focus、blur、mouseenter、mouseleave、mousemove、keydown、keyup、dragstart、drag、dragend、drop）
  3. states.py 定义状态名常量（value、checked、selected、text、visible、enabled、focused、hovered、readonly）
  4. errors.py 定义错误码与异常
- 验收命令：`python -m pytest tests/test_component.py -q`（期望：全部通过）
- 自检：派生尝试确实抛 TypeError；Event 只允许 obox 作为 src

### T5 请求对象与三种等待形态

- 步骤：
  1. 实现 Request：取消、完成、失败、超时四个状态转换
  2. 提供 result(timeout)、add_done_callback、__await__
  3. 测试阻塞完成、回调顺序、await 恢复、超时异常
- 验收命令：`python -m pytest tests/test_request.py -q`（期望：全部通过）
- 自检：重复完成与完成后回调都只生效一次

### T6 帧编解码

- 步骤：
  1. encode_frame 输出 4 字节大端长度加 UTF-8 JSON
  2. FrameDecoder 维护缓冲，支持半包与一次多帧
  3. 拒绝超过上限的帧长与非法 JSON
- 验收命令：`python -m pytest tests/test_framing.py -q`（期望：全部通过）
- 自检：中文与 emoji 往返一致；长度 0 与 1 的边界都有用例

### T7 命名管道服务端与客户端

- 步骤：
  1. server.py：QLocalServer 监听唯一管道名，accept 后校验 token 与协议版本，暴露 frame_received 与 disconnected
  2. client.py：QLocalSocket 连接、指数退避重试、握手、写帧
  3. 回环测试：服务端起在本机，客户端连上并收发一帧
- 验收命令：`python -m pytest tests/test_ipc.py -q`（期望：全部通过）
- 自检：token 错误时连接被拒；断开后能重连

### T8 消息总线

- 步骤：
  1. 实现 send、broadcast、request、on、off
  2. 关联表加超时定时器，应答到达即完成请求
  3. 拒绝广播应答；发送前校验 src 与本端身份一致
- 验收命令：`python -m pytest tests/test_bus.py -q`（期望：全部通过）
- 自检：超时后关联表为空；并发两个请求互不串号

### T9 组件解析器

- 步骤：
  1. 用 html.parser 子类把片段解析为 Node（tag、attrs、children、line、col）
  2. 未知标签与非法属性报错，错误信息带行列
  3. 测试嵌套、自闭合、注释忽略、非法标签
- 验收命令：`python -m pytest tests/test_parser.py -q`（期望：全部通过）
- 自检：错误定位到具体行号；空片段返回空列表而不是异常

### T10 组件注册表

- 步骤：
  1. 以命名空间（obox 或 名称.作者）为键维护 id 到组件的映射
  2. register 冲突时拒绝并报告；lookup 校验归属
  3. 视图销毁时按命名空间批量注销
- 验收命令：`python -m pytest tests/test_registry.py -q`（期望：全部通过）
- 自检：跨命名空间同名 id 不冲突；注销后 lookup 返回空

### T11 组件基类与 15 个组件

- 步骤：
  1. base.py：Component 基类，统一 read_state、write_state、emit_event
  2. 基于 qfluentwidgets 实现 Div、Text、Button、Input、TextArea、Checkbox、Radio、Switch、Select、Slider、Tag、Table、Tabs、Modal、Notification
  3. 每个组件至少支持一个状态读写，Button 与 Input 绑定点击与输入事件
- 验收命令：`python -m pytest tests/test_components.py -q`（期望：全部通过）
- 自检：15 个组件都能在 offscreen 平台实例化；未知状态名返回错误而不是静默

### T12 装配器

- 步骤：
  1. 遍历 Node 树生成控件树，把 id 注入注册表
  2. 事件回调转成 ComponentEventMessage 交给总线
  3. 任一层失败时整片回滚并注销已登记 id
- 验收命令：`python -m pytest tests/test_builder.py -q`（期望：全部通过）
- 自检：子树顺序与片段一致；回滚后注册表为空

### T13 QSS 过滤与主题

- 步骤：
  1. 约定扩展样式固定为 assets/style.qss，由 loader 扫描时登记，视图装配前应用；qss.py 解析规则块，按选择器白名单过滤（只允许组件 id 或扩展类名前缀）
  2. theme.py 加载全局主题 QSS
  3. 记录被拒规则与原因
- 验收命令：`python -m pytest tests/test_qss.py -q`（期望：全部通过）
- 自检：全局选择器与通配选择器都被拒；合法规则原样生效

### T14 扩展清单与目录扫描

- 步骤：
  1. manifest.py 定义字段与校验：name、version、publisher（即作者，构成 src 的 名称.作者 后缀）、description、main（固定为 extension.py）、icon、activationEvents、contributes
  2. icon 必须是 svg，icon 与 style.qss 的路径必须落在 assets 内，拒绝路径穿越
  3. loader.py 扫描 extensions/，非法目录跳过并收集错误
- 验收命令：`python -m pytest tests/test_manifest.py -q`（期望：全部通过）
- 自检：缺字段与路径穿越都有反例；合法扩展返回完整模型

### T15 扩展 context 与注册点

- 步骤：
  1. context.py：ExtensionContext 暴露 extension_id、assets_dir、storage_dir、register_command、register_view、send、request、subscriptions
  2. contributions.py：命令与视图注册表，支持按 id 查找与注销
  3. 测试注册、调用、注销
- 验收命令：`python -m pytest tests/test_context.py -q`（期望：全部通过）
- 自检：重复注册命令给出明确错误；context 销毁后订阅被清理

### T16 扩展宿主进程

- 步骤：
  1. host.py 入口：QCoreApplication 主循环加 asyncio 线程，握手后接收激活指令；v1 按清单顺序全量激活，activationEvents 只校验不参与调度
  2. 逐个激活扩展，捕获单个扩展异常并回传失败原因
  3. 消息分发到对应 context，停用时调用 deactivate
- 验收命令：`python -m pytest tests/test_host.py -q`（期望：全部通过）
- 自检：一个扩展激活失败后其他扩展仍被激活；停用后命令不可调用

### T17 宿主进程管理

- 步骤：
  1. supervisor.py 拉起子进程，传入管道名、协议版本与 token
  2. 监控进程退出，指数退避重启并重新握手
  3. 向上层发状态信号（已连接、已崩溃、已重启）
- 验收命令：`python -m pytest tests/test_supervisor.py -q`（期望：全部通过）
- 自检：连续两次崩溃不会无限重启；退出主程序时子进程被回收

### T18 主窗口与应用装配

- 步骤：
  1. main_window.py：FluentWindow 加导航与视图容器区，容器取值固定为 main（主区域）与 sidebar（侧栏），v1 不支持自定义容器
  2. app.py：创建 QApplication、注册内置组件、启动 supervisor、把扩展视图挂到容器
  3. main.py：命令行参数（--version、--extensions-dir），异常兜底与退出清理
- 验收命令：`python -m pytest tests/test_app_smoke.py -q`（期望：全部通过；用例内部设置 offscreen 平台并 3 秒后退出）
- 自检：宿主未就绪时界面仍能显示并提示；退出时宿主被回收

### T19 示范扩展

- 步骤：
  1. extension.json：name、version、publisher、description、main、icon（相对 assets）、activationEvents、contributes（commands 与 views）
  2. extension.py：activate 注册命令与视图，deactivate 清理；点击按钮后发 ComponentModifyMessage 改自己的文本
  3. assets：icon.svg、style.qss（只用自己的组件 id 选择器）、view.html（Div、Text、Button、Input）
- 验收命令：`python -m pytest tests/test_manifest.py -q -k demo`（期望：示范扩展清单校验通过）
- 自检：清单里的图标与视图路径都在 assets 内；QSS 不含全局选择器

### T20 端到端联调

- 步骤：
  1. 启动 obox（offscreen 或真实窗口），加载示范扩展
  2. 触发按钮点击，断言扩展收到事件并回改组件状态
  3. 杀掉宿主进程，断言 5 秒内重启并恢复扩展
- 验收命令：`python -m pytest tests/test_e2e.py -q`（期望：全部通过）
- 自检：日志里能看到事件往返与重连记录；失败时能定位到环节

### T21 文档与基线回填

- 步骤：
  1. README 的目录树与路线图按实现更新
  2. docs/arch.md 的 4.1 模块名与 8.2 性能按实测回填
  3. 跑基线校验
- 验收命令：`python C:/Users/chenzhi/.dsh/skills/df-validation/scripts/check.py --proj . --us US-20261120213402-0001-UI框架与扩展系统 --baseline-only`（期望：ok 为真）
- 自检：文档里没有与实现不符的路径；没有把计划写成既成事实

### T23 主界面三段式外壳

- 步骤：
  1. main_window.py 用 FluentWindow 的标题栏承载顶栏：左侧图标与 obox 标题，右侧最小化、最大化、关闭
  2. 中部左侧是固定宽度的图标栏，只放 svg 图标按钮；点击切换到内容栈里对应的视图
  3. 底部是扩展注册条，容器为 bottom 的视图渲染在这里；没有视图时隐藏
  4. app.py 按 view 的 container 取值挂载；host 回传视图时带上扩展图标路径
- 验收命令：`python -m pytest tests/test_app_smoke.py -q`（期望：全部通过，侧栏按钮数与注册视图数一致）
- 自检：无扩展时侧栏为空且底部栏不可见；有扩展时点击图标能切换视图

### T22 UI 自动化验证脚本

- 步骤：
  1. scripts/ui_driver.py：以 id 定位组件，发鼠标点击、键盘输入、截图；截图走窗口自绘抓取（QWidget.grab），必要时可切到整屏抓取
  2. scripts/verify_ui.py：启动 obox 与示范扩展，跑点击按钮、输入文本、读取状态三条场景，断言结果并落证据
  3. 产物：截图写 tmp/pics/场景名_时间戳.png，日志写 tmp/logs/verify_时间戳.log
- 验收命令：`python scripts/verify_ui.py`（期望：退出码 0，tmp/pics 有新截图，日志里三条场景均为 PASS）
- 自检：脚本不修改业务代码；无窗口环境下用 offscreen 也能跑完并产出截图

### T24 theme/light 组件库

- 步骤：
  1. 在 theme/light 下建包：组件基类（widget、owner、id、attach、container_layout、supported_states、state_accessors、supported_events、event_methods）
  2. 实现 15 个组件，状态用类型化方法（如输入框的 text 与 set_text），事件用具名注册方法（on_click、on_input 等）
  3. 写 theme.json（name、version、mode=light、entry）与浅色主题 QSS（圆角、淡边框、柔阴影、外壳配色）
- 验收命令：`uv run pytest -q tests/test_theme_light.py`（期望：15 个标签与状态映射断言全过）
- 自检：组件不 import obox 任何模块；标签小写后与现有取值一致

### T25 theme/dark 组件库

- 步骤：
  1. 复制 light 的结构，独立实现 15 个组件的深色外观与交互
  2. theme.json 的 mode 写 dark，QSS 给出深色外壳与组件配色
- 验收命令：`uv run pytest -q tests/test_theme_dark.py`（期望：标签与状态契约断言全过）
- 自检：与 light 的标签集合完全相同；状态映射覆盖同样的状态名

### T26 组件协议与校验

- 步骤：
  1. 定义协议：widget、attach、container_layout、supported_states、state_accessors、supported_events、event_methods
  2. 提供校验函数，检查映射里的方法在组件上存在、事件方法以 on_ 开头
  3. 单测覆盖缺失映射与拼错方法名
- 验收命令：`uv run pytest -q tests/test_component_protocol.py`（期望：全过）
- 自检：协议只依赖 PySide6 类型，不 import 任何具体组件实现

### T27 kit 加载器

- 步骤：
  1. 扫描 .theme 的每个子目录，解析 theme.json 并校验 name、version、mode、entry，汇总成可用套件清单
  2. 用 importlib 从 .theme/{name}/{name}.pyd 加载模块，调用 entry 取 provider
  3. 版本不符、文件缺失、导入失败分别给出明确异常
- 验收命令：`uv run pytest -q tests/test_kit_loader.py`（期望：全过）
- 自检：缺失 pyd 时不进入主窗口；错误信息包含路径

### T28 装配器与声明式事件

- 步骤：
  1. builder 接受 provider 的组件映射，不再静态 import 组件包
  2. 解析片段里的 on_ 前缀属性，只对声明过的事件调用组件的具名注册方法
  3. 状态读写按 state_accessors 走，未声明的状态在调用前拒绝
- 验收命令：`uv run pytest -q tests/test_builder.py tests/test_declarative_events.py`（期望：全过）
- 自检：未写 on_click 的按钮点击后消息队列为空；写了才有消息

### T29 启动选库与运行中切换

- 步骤：
  1. 读取 .obox/config.json 的 theme 字段，缺省 light；命令行参数覆盖
  2. 启动时加载 provider，应用主题并装配视图
  3. 切换请求：加载新 kit、销毁视图、重建；失败保留原 kit 并提示
- 验收命令：`uv run pytest -q tests/test_kit_switch.py`（期望：全过）
- 自检：切换后组件 id 重新注册；损坏 pyd 时进程不退出

### T30 Nuitka 构建脚本

- 步骤：
  1. 探测 MSVC，缺失时打印安装指引并退出非零
  2. 对 theme/light 与 theme/dark 分别执行 Nuitka --module，产物写 .theme/{name}/
  3. 复制 theme.json，失败时清理半成品
- 验收命令：`python scripts/build_theme.py`（期望：退出码 0，两套 pyd 与清单都存在）
- 自检：重复执行可覆盖；失败路径不留残缺目录

### T31 测试改造与 pyd 集成

- 步骤：
  1. 把现有组件与装配用例改为注入假 provider
  2. 新增一条集成用例，加载真实 pyd 并断言 15 个标签与元信息
  3. 让集成用例在 pyd 缺失时跳过并给出提示
- 验收命令：`uv run pytest -q`（期望：全过，集成用例在已构建时执行）
- 自检：不构建 pyd 时常规用例仍全过

### T33 删除旧组件包并迁移 demo

- 步骤：
  1. 删除 obox/ui/components 整包，确认没有残留 import
  2. demo 片段给按钮补 on_click 属性，其余需要事件的组件按需补 on_*
  3. 回归 scripts/verify_ui.py 与全量测试，确认点击仍能往返改状态
- 验收命令：`uv run pytest -q && uv run python scripts/verify_ui.py`（期望：全过，退出码 0）
- 自检：仓库里搜不到 obox.ui.components 的引用；demo 按钮带 on_click

### T32 视觉验收与文档

- 步骤：
  1. 用 scripts/verify_ui.py 分别跑 light 与 dark，截图存 tmp/pics
  2. README 补构建命令、theme 选择与运行中切换说明，并给出 .obox/config.json 的示例内容（含 theme 字段）
  3. 检查圆角、边框、阴影三项是否符合主题声明
- 验收命令：`uv run python scripts/verify_ui.py --theme dark`（期望：退出码 0，截图落 tmp/pics）
- 自检：两种主题的外壳与内容区颜色一致地变化

## 测试策略

常规：先实现后补测试，每个任务跑自己的验收命令；另加脚本化 UI 验证，由 scripts/verify_ui.py 驱动，截图落 tmp/pics、日志落 tmp/logs。

## 执行顺序

1. T1
2. T2 ∥ T3
3. T4 ∥ T5 ∥ T6 ∥ T9 ∥ T14
4. T7 ∥ T8 ∥ T10 ∥ T15
5. T11 ∥ T13 ∥ T16
6. T12 ∥ T17
7. T18 ∥ T19
8. T22 ∥ T23
9. T20
10. T21
11. T26
12. T24 ∥ T25 ∥ T27
13. T28
14. T29 ∥ T30
15. T31
16. T32
17. T33

## 覆盖检查

- 扩展目录与清单：T1、T14、T19、T21
- 主界面三段布局：T23
- 扩展生命周期与上下文注入：T15、T16、T18
- HTML 组件声明与装配：T9、T11、T12、T18
- 组件标识唯一性：T10、T12
- 组件事件上报：T4、T8、T11、T12、T20、T22、T28
- 界面套件清单与加载：T27、T29
- 界面提供者契约：T26、T27
- 组件契约不变：T24、T25、T31、T33
- 视觉统一：T24、T25、T32
- 运行中切换 kit：T29
- 构建与 pyd 产物：T30
- 组件能力接口与消息处理分界：T26、T28
- 测试链路：T31
- 组件状态查询：T4、T8、T11、T20
- 组件状态修改：T4、T8、T11、T20、T22
- 消息基类与广播语义：T3、T8
- 请求应答与异步等待：T5、T8
- 进程间通道：T6、T7、T16、T17
- QSS 样式作用域：T13
- 注册点：T15、T18、T19
- 扩展故障隔离：T16、T17、T20

## 自检（落盘前）

- [x] 每条需求都被至少一个任务覆盖
- [x] 每个任务都有可复制执行的验收命令
- [x] 依赖无环，同波次内文件不重叠
- [x] 方式只取主 Agent、subagent、后台
- [x] 模板占位符与注释全部替换