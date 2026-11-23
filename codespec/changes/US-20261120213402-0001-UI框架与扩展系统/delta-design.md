---
status: done
---

# UI 框架与扩展系统 Delta Design

## Context

工程是绿地：当前只有 pyproject.toml、打印一行文本的 main.py 与空的 README，没有 PySide6 与 qfluentwidgets。基线 design.md 的 D1 到 D8 已把方向定死（原生控件承载 HTML DSL、命名管道、单宿主进程、消息方向拆分与返程、自建 Future、QSS 白名单、主窗口挂载、宿主双循环），delta-spec 只有一条 ADDED（主界面三段布局），其余需求与基线一致。因此本文件不重新论证方向，只把 D1 到 D8 落成模块划分、文件布局、错误语义与实施顺序，并预告合并时基线要补哪几条决策。

第二轮追加：组件实现从 obox/ui 迁到 theme/light 与 theme/dark 两个独立主题包，各自用 Nuitka 编译为 pyd 放到 .theme/{name}/；obox 运行期按配置加载并可切换，因此装配器改为依赖注入 provider，外壳主题也改由 kit 提供。

## Scope

本次需求侧只新增一条（主界面三段布局），其余沿用基线 13 条。实现范围是这 14 条需求，落地为 obox 主程序包与 extensions/demo 示范扩展。

不在本次范围：按扩展分包的多进程形态、扩展签名与权限声明、组件热重载、表格类组件的复杂能力（排序、虚拟滚动、列固定）、非 Windows 平台验收。

第二轮范围：theme/light 与 theme/dark 两套独立组件实现（各 15 个）、Nuitka 构建脚本、obox 启动扫描 .theme 形成可用套件清单并按配置选中一套、运行中切换与失败回滚、外壳主题随 kit、测试改为假 provider 加一条真实 pyd 集成用例。仍不在范围：设置界面里的套件选择（下一轮）、kit 的签名与在线分发、换库时的状态迁移、非 Windows 平台。

## Changes

| 模块路径 | 改动 | 对齐的基线需求 | 结构影响 |
|---|---|---|---|
| obox/main.py、obox/app.py | 新增：入口解析命令行、创建 QApplication、装配主窗口、启动宿主管理器 | 扩展生命周期、故障隔离 | 新增入口层，只做组装 |
| obox/api/message.py | 新增：Message 基类（src、dst、msg_id、reply、correlation_id、payload）与消息类型常量、序列化往返 | 消息基类与广播语义 | 契约层无反向依赖 |
| obox/api/component.py | 新增：三条组件消息，固定 msg_id、禁止扩展派生、方向校验 | 事件上报、状态查询、状态修改 | 契约层新增三个不可继承类型 |
| obox/api/events.py、obox/api/states.py | 新增：事件名与状态名的枚举常量（click、input、checked 与 value、checked、focused 等） | 事件上报、状态查询与修改 | 契约层新增两套常量 |
| obox/api/request.py | 新增：请求对象，支持阻塞等待、回调、await 三形态与超时清理 | 请求应答与异步等待 | 契约层新增协程桥 |
| obox/api/errors.py | 新增：错误码与异常类型（组件不存在、id 冲突、越权、帧非法、超时、广播应答） | 状态查询、修改与广播语义 | 契约层新增错误目录 |
| obox/core/bus.py | 新增：消息路由、订阅表、关联表与超时定时器 | 消息基类、请求应答 | 运行层依赖契约层，不依赖界面 |
| obox/core/ipc/framing.py、server.py、client.py | 新增：长度前缀帧编解码、obox 侧监听与握手、宿主侧连接与重连 | 进程间通道 | 运行层新增传输子包 |
| obox/ui/parser.py | 新增：HTML 片段解析为节点树，未知标签与非法属性给出行列错误；保留 on_ 前缀属性供装配阶段做事件订阅 | HTML 组件声明与装配、组件事件上报 | 表示层新增解析器 |
| obox/ui/registry.py | 新增：以扩展命名空间为键的组件注册表，重复 id 拒绝 | 组件标识唯一性 | 表示层新增注册表 |
| obox/ui/builder.py | 新增：节点树装配为 QWidget 树，绑定事件上报与状态读写 | HTML 组件声明与装配、事件上报 | 表示层新增装配器，依赖 qfluentwidgets |
| obox/ui/qss.py、obox/ui/theme.py | 新增：全局主题加载与扩展 QSS 选择器白名单过滤；扩展样式固定为 assets/style.qss，由扩展层登记后交给表示层应用 | QSS 样式作用域 | 表示层新增样式子模块 |
| obox/ui/main_window.py | 新增：三段式外壳，顶栏为图标、标题与窗口按钮，中部为图标侧栏与内容栈，底部为扩展注册条 | 注册点、主界面三段布局 | 表示层新增主窗口，容器取值扩为 main、sidebar、bottom |
| obox/ui/components/ | 新增：Component 基类与 15 个组件（Div、Text、Button、Input、TextArea、Checkbox、Radio、Switch、Select、Slider、Tag、Table、Tabs、Modal、Notification） | HTML 组件声明、事件、状态查询与修改 | 表示层新增组件包，只依赖契约层与 qfluentwidgets |
| obox/extensions/manifest.py、loader.py | 新增：extension.json 模型、字段与路径校验、目录扫描；icon 限 svg，登记 style.qss 供装配时应用 | 扩展目录与清单 | 扩展层新增扫描与校验 |
| obox/extensions/supervisor.py | 新增：宿主子进程拉起、握手、监控、崩溃重启 | 进程间通道、故障隔离 | 扩展层新增进程管理 |
| obox/extensions/host.py、context.py、contributions.py | 新增：宿主主循环与 asyncio 线程、ExtensionContext、命令与视图注册表 | 生命周期与上下文、注册点 | 扩展层新增宿主入口，可被 python -m 拉起 |
| obox/assets/obox.svg | 新增：从 tmp/obox.svg 迁入的主程序图标 | 扩展目录与清单（图标约定） | 静态资产新增 |
| extensions/demo/ | 新增：示范扩展（清单、activate/deactivate、svg 图标、QSS、HTML 视图） | 全部需求的端到端验证 | 新增首个扩展目录 |
| tests/ | 新增：帧编解码、消息序列化、解析器、注册表、清单校验的单元测试 | 支撑上述需求的验收 | 新增测试包 |
| theme/light/ | 新增：15 个组件类、组件基类、自带事件与状态常量、theme.json 清单与浅色主题 QSS（含外壳） | 组件契约不变、视觉统一 | 组件实现迁出 obox/ui；编译产物为 .theme/light/light.pyd |
| theme/dark/ | 新增：独立的 15 个组件类与深色主题 QSS，标签与状态契约与 light 一致 | 视觉统一、运行中切换 | 与 light 同构、独立维护，编译产物为 .theme/dark/dark.pyd |
| obox/ui/components/ | 删除：组件实现迁到 theme 两套库后不再保留 | 组件契约不变 | 表示层只剩装配与加载 |
| extensions/demo/ | 修改：片段里的按钮补 on_click，按新的声明式订阅触发事件 | 组件事件上报 | 示范扩展跟随新契约 |
| scripts/build_theme.py | 新增：调用 Nuitka 把 theme/{name} 编译为 .theme/{name}/{name}.pyd，复制 theme.json，失败非零退出 | 构建与 pyd 产物 | 新增构建入口，依赖 MSVC |
| obox/ui/kit.py | 新增：扫描 .theme 汇总可用套件、theme.json 解析、pyd 加载、版本与缺失校验、切换入口 | 界面套件清单与加载、界面提供者契约 | 表示层新增加载器，隔离 importlib 细节；设置界面选择留待下一轮 |
| obox/ui/builder.py | 修改：组件类由 provider 注入，按 supported_states 与 event_methods 绑定状态读写与事件回调 | provider 契约、组件能力接口 | 装配器去掉对具体实现的依赖，改用声明式映射 |
| obox/ui/component_protocol.py | 新增：组件协议（supported_states、state_accessors、supported_events、event_methods、widget、attach、container_layout）与校验 | 组件能力接口与消息处理分界 | 表示层新增协议模块，kit 按结构化协议实现 |
| obox/ui/main_window.py、obox/ui/theme.py | 修改：外壳样式改由 provider 主题驱动；新增销毁并重建视图的入口 | 视觉统一、运行中切换 | 主窗口不再持有固定 QSS |
| obox/app.py | 修改：启动按配置加载 kit；缓存每个视图的 owner、html、container 与标题；切换时销毁视图、换 provider、按缓存重建 | 运行中切换 | 装配流程加入 kit 生命周期与视图定义缓存 |
| tests/ | 修改：常规用例注入假 provider；新增一条加载真实 pyd 的集成用例 | 测试链路 | 用例不再 import 组件实现 |
| README.md | 修改：补构建命令、theme 选择与切换说明 | 构建与 pyd 产物 | 门面补充使用方式 |

## Baseline Diff

合并时基线要动的地方，按文件列出。

| 基线文件 | 章节 | 变为什么 |
|---|---|---|
| codespec/specs/design.md | Decisions | 新增三条实施级决策：D9 连接采用一次性 token 握手与协议版本号；D10 错误码目录与请求失败语义（组件不存在、id 冲突、越权、帧非法、超时、广播应答）；D11 模块文件布局（obox/api、obox/core、obox/ui、obox/extensions 四个子包与 extensions 根目录）；并把 D7 补成三段式外壳：侧栏只放图标，底部栏是第三个注册区 |
| codespec/specs/design.md | Context | 首行「尚未实现」在实现完成后改为已实现版本号与实测结论 |
| docs/arch.md | 4.1 分层与模块架构图 | 模块名以真实文件路径替换为最终形态；若组件清单与实现有出入，同步修正 |
| docs/arch.md | 8.2 性能 | 用实测的往返延迟与首屏装配耗时替换当前目标值 |
| README.md | 目录结构、路线图 | 目录树与实现对齐；路线图把已交付项打勾 |
| codespec/specs/spec.md | Requirement: 组件事件上报 | 整节替换为「只有片段声明 on_ 属性才投递」，并补三条场景 |
| codespec/specs/design.md | D11 模块布局 | 改为：组件实现位于 theme/{light,dark}，构建产物在 .theme，obox 只保留装配、加载与外壳 |
| codespec/specs/design.md | D1 渲染栈 | 补一句：装配器从 provider 取组件类，obox 不再静态依赖具体组件包 |
| docs/arch.md | 4.1 分层图、7.1 进程拓扑 | 增加 theme 源码与 .theme 产物节点，以及 pyd 加载边 |
| docs/arch.md | 8.2 性能 | 补 pyd 加载耗时与切换重建耗时的实测值 |
| README.md | 快速开始、目录结构 | 补 theme/、.theme/ 与构建命令，说明换库方式 |

## Risks / Rollback

| 风险 | 触发条件 | 影响 | 应对 |
|---|---|---|---|
| qfluentwidgets 与 PySide6 版本不兼容 | 首次安装 | 主程序无法启动 | 先固定 PySide6 版本区间再装组件库，失败则降级到纯 Qt 控件并记录 |
| 命名管道在 Windows 上握手失败 | 服务端未就绪即连接 | 扩展全部加载失败 | 宿主侧带退避重连，服务端先 listen 再拉起子进程 |
| 组件 id 冲突策略过严 | 视图重建时复用 id | 重复渲染失败 | 视图销毁时按命名空间批量注销，重建前清空 |
| QSS 白名单误杀 | 复杂选择器 | 扩展样式不生效 | 记录被拒规则与原因，提供调试开关 |
| 双循环桥接丢消息 | 线程切换处异常 | 请求挂起 | 关联表超时兜底，桥接处只投递不阻塞 |
| Nuitka 构建慢 | 每次改组件都要编译 | 开发循环被拖住 | 常规用例用假 provider；只有集成用例依赖构建 |
| 构建机缺 MSVC | 没有 C 编译器 | 无法产出 pyd，程序起不来 | build_theme.py 先探测编译器，缺失时给出安装指引并退出 |
| 旧 pyd 常驻内存 | 反复切换套件 | 内存随切换增长 | 文档写明限制，提示多次切换后重启；切换次数不做硬限制 |
| 两套组件实现漂移 | light 与 dark 各自演化 | 同一片段在两套下表现不一致 | 契约常量抽到共用模块，集成用例对两套都断言标签与状态 |

回滚方式：实现全部落在新增的 obox/ 与 extensions/ 目录，main.py 保持可运行的最小入口；回滚即删除新增目录、恢复 pyproject.toml 的依赖声明，工程回到只有脚手架的状态。

## Assumptions

- PySide6 与 PySide6-Fluent-Widgets 允许从 PyPI 安装，开发机可联网。
- 主程序与宿主共用同一个 Python 解释器与虚拟环境，宿主通过 python -m obox.extensions.host 拉起。
- 示范扩展只用标准库与 obox/api，不引入第三方依赖。
## 第五轮：移除第三方控件库

| 模块 | 改动 | 对齐的需求 |
|---|---|---|
| theme/{light,dark}/components/*.py | 按钮、输入、选择、滑块、表格、页签、标签换纯 Qt 控件；复选框、单选、开关改为自绘；toast 与浮层自绘 | 不依赖第三方控件库 |
| theme/{light,dark}/theme.py | 补自绘控件（tab、toast、modal、primary 按钮）与 QSS 细节 | 不依赖第三方控件库 |
| obox/ui/main_window.py | 标签换 QLabel，提醒换自绘 toast | 不依赖第三方控件库 |
| obox/app.py | 删除 setTheme / Theme 依赖，配色全部由套件 QSS 负责 | 不依赖第三方控件库 |
| pyproject.toml | 移除 PySide6-Fluent-Widgets | 不依赖第三方控件库 |

取舍：控件库提供的是观感与动画，代价是外观锁定、主题只能靠它的 API 改；换成纯 Qt 后 всё由套件 QSS 与我们自己的绘制决定，代价是复选框/单选/开关要自己画。

### i18n 与 OML

| 模块 | 改动 | 对齐的需求 |
|---|---|---|
| obox/i18n.py | 新增：注册表，按 (name, id) 存 BCP-47 文案，translate 负责替换 i18n 引用（双花括号包住 i18n 与条目 id） | i18n 注册与占位替换 |
| obox/api/i18n.py | 新增：I18nRegisterMessage，扩展注册文案时发给 obox | i18n 注册与占位替换 |
| obox/extensions/context.py | 修改：新增 register_i18n；register_view 的第二个参数改为 oml 路径或内联片段 | 两条需求 |
| obox/oml.py | 新增：读取扩展目录下的 .oml，拒绝越界与缺失 | 视图文件格式 |
| obox/app.py | 修改：启动注册 obox 自身文案；处理 i18n 消息；挂载视图时读 oml 并先做替换 | 两条需求 |
| extensions/demo、extensions/gallery | 修改：视图改为 views/*.oml；demo 注册中英文文案并在 oml 里使用占位符 | 两条需求 |
| obox/ui/title_bar.py、main_window.py | 修改：标题栏加语言按钮与菜单，切换后回调宿主重建 | i18n 注册与占位替换 |
| obox/app.py | 修改：switch_language 重建视图、写配置并同步菜单 | i18n 注册与占位替换 |

### 动画实现

自绘控件把过渡量暴露成 Qt Property（开关 `knob`、复选与单选 `progress`），用 `QPropertyAnimation` + OutCubic 驱动重绘；提醒、通知、浮层用 `QGraphicsOpacityEffect` 的 `opacity` 做淡入淡出。动画对象在结束后自动回收（DeleteWhenStopped），不进入消息链路。