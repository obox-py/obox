---
status: done
---

# Design

> 架构与图形在 docs/arch.md；本文件只写决策与风险。

## Context

obox 已按本文件落地：Python 3.12.7、PySide6 6.12.0。主程序包在 obox/ 下（api、core、core/ipc、ui、extensions 五个位置），组件实现独立在 theme/light 与 theme/dark，编译为 pyd 后由 obox 从 .theme 加载；示范扩展在 extensions/demo/；主程序与扩展宿主子进程跑在两个进程里，用 Windows 命名管道相连。硬约束仍是：Windows 优先、不使用网络端口、扩展只写 Python 与静态资产、界面用 Qt 原生控件与自绘（未引入 Web 引擎，也不依赖第三方组件库）。

## Goals / Non-Goals

**Goals:**

- 三块地基（HTML 组件 DSL 与 QSS、命名管道消息层、扩展宿主）在同一版本内可运行。
- 组件消息闭环跑通：事件上报、状态查询、状态修改，且请求能异步取回结果。
- 扩展目录、清单、生命周期与 context 与 VSCode 同构，第三方可照文档写扩展。
- 组件 id 在扩展命名空间内唯一，跨扩展隔离，越权修改被拒绝。
- 一份示范扩展可演示全部主链路。

**Non-Goals:**

- 不做全量 antd 组件（本期 12 到 15 个）。
- 不做扩展商店、签名、权限模型、热重载。
- 不做多平台验收与高 DPI、主题定制矩阵。
- 不做扩展间直接通信（一律经 obox 中转）。

## Decisions

### D1 HTML 组件 DSL 由 Qt 原生控件与自绘承载

- 选择：扩展写 PascalCase 组件标签的 HTML 片段；obox 用基于 html.parser 的轻量解析器解析标签，按当前主题套件（provider）给出的组件映射实例化，属性映射为构造参数，组装成 QWidget 树；样式由套件主题 QSS 与扩展级 QSS 共同决定。
- 理由：与 html+qss+message 的原始意图一致；原生控件由套件自己绘制与定色，外观完全可控；无需 Web 运行时。
- 演进：早期用 Fluent 控件库起步，第五轮已全部换成纯 Qt 控件与自绘，依赖只剩 PySide6。
- 否掉的替代：QWebEngineView 加 HTML/CSS —— 与 QSS 要求冲突、安装体积增加 150MB 以上、扩展界面与桌面外壳变成两套渲染路径；从零实现 HTML/CSS 渲染引擎 —— 范围失控。

### D2 进程通道用 QLocalServer 与 QLocalSocket 命名管道

- 选择：obox 侧 QLocalServer 监听唯一管道名（含会话与实例标识），扩展宿主侧 QLocalSocket 连接；帧为 4 字节大端长度加 UTF-8 JSON。
- 理由：Windows 上就是命名管道，Qt 原生异步、跨平台、不占端口；JSON 便于调试与跨语言。
- 否掉的替代：WM_COPYDATA（载荷上限、同步阻塞、需要原生窗口过程桥接）；TCP 回环端口（违反约束）；共享内存加事件（实现与调试成本高）。

### D3 单一扩展宿主进程

- 选择：obox 启动一个扩展宿主子进程（python -m obox.extensions.host），所有扩展在其中激活；宿主崩溃后 obox 重启并重新激活。
- 理由：与 VSCode 的 extension host 同构；扩展共享一个解释器，组件消息只需一条通道。
- 否掉的替代：每扩展一进程 —— 消息要按扩展路由、进程池与生命周期管理复杂；宿主内线程隔离 —— 抵御不了段错误与死循环。

### D4 组件消息方向拆分与返程标识

- 选择：ComponentEventMessage 由 obox 发出（src 为 obox，dst 为创建者扩展）；ComponentStateMessage 与 ComponentModifyMessage 由扩展发出（src 为扩展，dst 为 obox）。所有消息带 reply 布尔标识与 correlation_id；应答复用同一消息类型并置 reply 为真；dst 为空的广播消息不接受应答。
- 理由：事件发生在 obox 渲染的控件上，由 obox 上报才是真实方向；状态必须能取回值，只能靠应答；复用原消息类型避免消息类型爆炸。
- 否掉的替代：三条消息一律固定 src 为扩展、dst 为 obox（事件要靠 obox 以扩展名义绕行投递，语义扭曲）；为应答新增独立消息类（违背复用原有消息的要求）。

### D5 自建 Future，同时支持阻塞、回调与 await

- 选择：obox/api 提供请求对象：发送返回 Future，支持带超时的阻塞等待、add_done_callback 回调与 await 协程；超时后以 TimeoutError 结束并从关联表移除。
- 理由：obox 侧主循环是 Qt，扩展宿主侧是 asyncio；一个对象覆盖两种等待形态，不必引入 qasync。
- 否掉的替代：只提供回调（扩展代码难写）；只提供阻塞（obox 主线程被卡死）；引入 qasync（增加依赖与循环绑定的复杂度）。

### D6 QSS 两层作用域与选择器过滤

- 选择：obox 内置全局主题 QSS；扩展可在 assets 下提供 QSS，加载前用选择器白名单过滤，只保留以组件 id 或扩展组件类名为前缀的规则，其余拒绝并记录。
- 理由：既让扩展定制外观，又不污染 obox 与其他扩展。
- 否掉的替代：只给全局主题（扩展无法定制）；允许任意注入（样式互相踩踏）。

### D7 扩展视图寄生在主窗口容器内

- 选择：扩展通过 views 注册点声明视图，容器取值为 main、sidebar 与 bottom：main 进内容栈，sidebar 在左侧图标栏占一个 svg 图标，bottom 进底部注册条（无注册时隐藏）。组件树由 obox 进程渲染，扩展进程只持有逻辑。
- 理由：与桌面外壳一致，主题与布局统一管理。
- 否掉的替代：每扩展独立窗口（与主窗口割裂、焦点管理复杂）；扩展自带 WebView（引入 Web 运行时，与 D1 冲突）。

### D8 宿主内双循环：Qt 管通道，asyncio 跑扩展

- 选择：扩展宿主主线程跑 QCoreApplication 处理 QLocalSocket I/O；另起线程跑 asyncio 事件循环执行扩展协程；两者通过线程安全队列与信号桥接，消息到达即完成对应 Future。
- 理由：QLocalSocket 天然属于 Qt 事件循环；扩展要写 async 与 await，需要 asyncio 循环；分线程避免互相阻塞。
- 否掉的替代：纯 asyncio 实现命名管道客户端（Windows 上要依赖 Proactor 的私有接口）；纯 Qt 单循环（扩展里无法 await）。

### D9 一次性 token 握手与协议版本

- 选择：obox 每次启动生成随机管道名与一次性 token，监听完再拉起宿主；宿主连上后先发 hello（协议版本加 token），服务端校验通过回 welcome，之后才收发消息。
- 理由：命名管道对同机进程可见，握手是唯一能挡住冒充者的位置；协议版本让两端不兼容时快速失败而不是收错消息。
- 否掉的替代：不握手（任何本机进程都能接进来）；用 PID 校验（PID 可伪造且会复用）。

### D10 错误码与请求失败语义

- 选择：错误以 error 与 message 两个字段随应答 payload 返回；请求方超时由关联表兜底并清理；广播消息与返程互斥，对广播发应答直接报错。
- 理由：跨进程只能传数据，异常类型无法序列化，错误码是唯一稳定的契约；超时兜底保证请求不会永久挂起。
- 否掉的替代：把异常栈序列化过去（不安全且体积大）；不发应答只靠超时（请求方分不清慢与失败）。

### D11 模块布局与依赖方向

- 选择：obox/api、obox/core（含 ipc）、obox/ui、obox/extensions 四个子包；组件实现放在 theme/light 与 theme/dark，编译为 pyd 落到 .theme；扩展有两个来源：开发目录 extensions/ 与安装目录 .obox/extensions（.oix 解包后）。api 是纯 Python 契约层，ui 与 extensions 都依赖 api 与 core，彼此不互相依赖；套件不依赖 obox，靠结构化协议对接。
- 理由：字符串级契约两边都要导入，放在 api 里避免宿主进程拖进界面依赖；依赖单向让宿主进程可以只装 core 而不装 ui。
- 否掉的替代：单包平铺（导入宿主时会连带加载 QWidget）；把契约放进 ui（宿主必须装 GUI 依赖）。

### D12 主题套件独立成包并编译为 pyd

- 选择：light 与 dark 各自是独立源码包（theme/{name}），用 Nuitka 编译为 .theme/{name}/{name}.pyd；obox 启动扫描 .theme 形成可用清单，按配置（缺省 light）加载；运行中可切换，切换时销毁视图重建，旧模块常驻内存。套件同时提供色板、圆角、控件高度与间距参数，装配器按参数排布。
- 理由：组件实现与主题绑定，换套件即换整套外观；编译成扩展模块后发布物是二进制，源码不必随包分发。
- 否掉的替代：组件留在 obox/ui（无法替换）；Cython 或 pybind11（用户选择 Nuitka）；运行中卸载旧 pyd（CPython 不支持卸载扩展模块）。

### D13 声明式事件订阅

- 选择：片段用 on_ 前缀属性声明需要的事件（如 on_click），obox 只对声明过的事件调用套件的具名注册方法；未声明的交互不产生消息。属性值只作标记。
- 理由：扩展能精确控制消息量，obox 侧不需要为每个事件都绑一遍；未声明的事件在装配阶段就被跳过。
- 否掉的替代：默认订阅组件全部事件（消息噪音大）；用属性值指定 handler 名（需要额外的扩展侧路由表）。

### D14 弹性布局由套件提供

- 选择：Flex 容器与自定义 QLayout 放在两套套件里，支持 direction、wrap、justify、align、gap 与子项 grow；obox 只负责把子项挂进布局并按 sizeHint 与最小尺寸计算。
- 理由：CSS 的换行与按剩余空间伸缩用 Qt 盒子嵌套拼不出来；布局放在套件里，换主题时布局行为可随套件演进。
- 否掉的替代：QBoxLayout 嵌套（不支持换行）；给 Div 加 flex 属性（两种布局语义混在一个标签）。

### D15 扩展编译为 pyd 并打包为 .oix

- 选择：打包脚本按 import 图把扩展目录内的 Python 文件逐个编译为同名 pyd，连同清单、i18n.json、assets 与 views 打成 zip（.oix）；安装即解压到 .obox/extensions/{id}，加载时把目录加入 sys.path，入口优先 extension.pyd。
- 约束：运行期依赖必须落在 import 图内，扩展不得用 exec 或读取兄弟源码文件的方式取数据，否则安装后会因缺文件激活失败。
- 理由：分发物不含源码；逐文件编译与「按名字 import 兄弟模块」的运行方式一致，装进 sys.path 就能解析。
- 否掉的替代：合并成单个 pyd（Nuitka 对非包结构支持差，且兄弟模块无法按名字 import）；只打源码 zip（隐藏不了实现）；自包含第三方库（体积与数据文件问题）。

### D42 扩展读取自己的配置

- 选择：obox 在扩展激活后与设置写入后，用 EXTENSION_CONFIG_MSG 把该扩展前缀下的配置值（values + defaults，键为属性名）发给扩展；扩展以最后一条为准。
- 理由：设置页原本只写值，扩展拿不到自己的配置；独立消息不改变设置页结构，也避免扩展反查宿主。
- 否掉的替代：扩展直接读 config.json（越过宿主、并发写风险）；设置值随激活参数传入（变更时无法通知）。

### D43 Windows 能力封在扩展内

- 选择：DPAPI、cmdkey、mstsc、Chrome 探测都由扩展自己实现（ctypes/winreg/subprocess），宿主不提供封装；非 Windows 平台先判平台并返回提示。
- 例外：宿主自身的开机自启动由 obox/core/autostart.py 用 winreg 直接读写 HKCU Run，因为自启动指向 obox.exe 本身，宿主不启动自己就没法由扩展代管。
- 理由：这些能力只服务个别扩展，放进宿主会扩大核心面；扩展独立发版时可各自升级。
- 否掉的替代：宿主提供系统能力 API（跨平台抽象成本高，且宿主无权代管子进程）。

### D44 主题与扩展双源目录

- 选择：主题从安装目录 themes/（源码态回退 .theme）与数据目录 themes/ 扫描，同名用户优先；扩展从安装目录 extensions/、数据目录 extensions/ 与源码 extensions/ 加载，同名按「用户 > 系统 > 源码」。
- 理由：安装包自带系统资源，用户可覆盖与扩展，不改安装目录。
- 否掉的替代：全部放数据目录（首次启动要解包、升级需迁移）；只读安装目录（用户无法扩展）。

### D45 按架构分发与安装

- 选择：安装包与 oix 都带 x86_64/arm64 标识；oix 内入口为 extension.pyd，安装时以文件名后缀与进程架构比对，不匹配拒绝；构建用 GitHub Actions 的 windows-latest 与 windows-11-arm 矩阵。
- 理由：pyd 与架构绑定，不能通用；托管 ARM runner 已可用，PySide6 6.12 有 win_arm64 轮子。
- 否掉的替代：只发 x64（ARM 设备需自行编译）；发源码 zip（违背 pyd 分发）。

### D46 语言集合固定为四种并统一存码

- 选择：可选语言固定为 zh-CN、zh-HK、zh-TW、en-US，配置里只存 BCP-47 码，列表由宿主常量给出并用测试守护覆盖度；旧配置里的地区标签在启动时映射成码并写回。
- 理由：QLocale 全量枚举会列出上百种语言，而文案只能覆盖有限集合，列出来却回退中文比不列更差；存码则避免标签随 Qt 本地化改名而漂移。
- 否掉的替代：按已注册文案动态求交集（随扩展加载时序抖动）；继续用地区标签（与设置读写的场景冲突）。

### D47 扩展文案由宿主按命名空间替换占位符

- 选择：扩展不持有翻译表，把用户可见文案写成 i18n 占位符经消息传给宿主（视图数据、组件状态修改、侧栏标题、对话框与 app 卡片标题），宿主在渲染点按该扩展的命名空间替换；未注册的占位符原样保留。
- 理由：翻译表只在宿主侧加载，语言切换时重建视图即可全量生效，不必重启扩展进程。
- 否掉的替代：给扩展下发文案表（多一条同步通道，切换语言要重启宿主）；扩展自备多语言文件（与 obox/i18n.json 两套事实）。

## Risks / Trade-offs

- 单宿主进程：一个扩展段错误会带走全部扩展；缓解：崩溃自动重启宿主并提示，后续可演进为按扩展分包。
- 管道安全：命名管道可被本机任意进程连接；缓解：连接时校验一次性 token，管道名带随机后缀。
- QSS 过滤是字符串级白名单，复杂选择器可能误判；缓解：解析失败时拒绝整份样式并给出原因。
- HTML DSL 与 antd 的语义差异（Table、Form 校验等）会被简化；缓解：先覆盖核心交互，复杂组件单独迭代。
- 组件消息高频时 JSON 序列化成为瓶颈；缓解：先测量，必要时换二进制编码或批量合并。
### D18 模板指令与局部更新

- 选择：OML 支持 o-for、o-if 与双花括号绑定；装配时记录文本绑定与区域对象，数据变化只更新绑定文本、重建指令区域。
- 理由：网格这类列表需要按数据渲染；整树重建会丢状态，局部更新能保住其余组件实例。
- 否掉的替代：整树重建（丢输入内容）、完整虚拟 DOM diff（成本过高）。

### D19 应用页与窗口复用

- 选择：应用页由 extensions/app 系统扩展提供，网格用 o-for 渲染；obox 按 app_id 管理窗口，single 与 persistent 控制复用与关闭行为。
- 理由：应用是扩展间协作，走消息解耦；持久化只保留窗口对象，不做状态序列化。
### D20 应用搜索与扩展同步

- 选择：过滤放在 App 扩展（它持有列表、能按标题/描述/作者做子串匹配），结果经 APP_VIEW_DATA_MSG 回注；obox 只校验 owner 与已知 id 后更新视图数据。目录用 QFileSystemWatcher 监听，变化后去抖 400ms 重启宿主。
- 理由：过滤属于应用层策略，宿主只做数据与安全边界；重启宿主复用已有的激活与推送链路，不新增增量扫描。
- 代价：扩展增删会触发一次宿主重启，正在运行的应用窗口会被关闭重建。
### D21 容器语义与设置

- 选择：容器只保留 sidebar 与 bottom，删除 main；设置做成系统扩展 extensions/settings，设置项由 obox 汇总（内置项 + 扩展 configuration）后推送，写入经 SETTINGS_SET 落到 .obox/config.json。
- 理由：main 语义不清；设置属于界面但数据与持久化归宿主，扩展只负责渲染与交互。
- 代价：旧清单写 main 会被拒绝；设置控件只支持 bool/string/enum。
### D22 Agent 技能包

- 选择：把扩展开发、主题开发、界面验证、测试检查沉淀成 .agents/skills 下的四个技能，按对象切分，每个带 references/templates/scripts。
- 理由：agent 需要可执行的入口而不是散落的文档；脚本复用现有 obox 模块与 scripts，避免实现分叉。
- 代价：技能内容需要随代码演进维护，校验脚本依赖 .theme 构建产物。
### D23 安装形态与路径

- 选择：Nuitka standalone 出 obox.exe，安装目录含 .theme 与已解压的 extensions/{app,settings}；程序目录只读，数据目录固定 %LOCALAPPDATA%\\obox；扩展扫描三根，优先级用户安装 > 系统 > 源码。
- 理由：目标机不需要 Python；系统扩展随装即用，不经过 .oix 安装；数据目录可写避免 Program Files 权限问题。
- 代价：安装包体积大、构建慢；三根并存需要日志说明覆盖关系。
### D25 托盘与关闭行为

- 选择：按用户命名管道实现单实例，第二实例发送 show 后退出；QSystemTrayIcon 常驻；关闭决策抽成 decide_close 纯函数，设置页「行为」分类存 close_action（ask/tray/quit），询问对话框为自绘 QDialog。
- 理由：管道按用户隔离且无需文件锁；纯函数便于测试；对话框自绘保持视觉一致。
- 代价：托盘在无桌面会话不可用时退化为直接退出；询问对话框阻塞自动化，验证脚本需先 allow_close。
### D27 参考图视觉规范

- 选择：按 tmp/light.png 与 tmp/dark.png 采样重做两套主题：主色 #2f6bee / #5b8def，圆角 2px，控件高 32，按钮四 variant，方形勾选/单选，主题自带 HarmonyOS Sans SC 并在启动时注册为应用字体。
- 理由：参考图是唯一视觉基准；字体随主题走，切换套件仍用对应字体。
- 代价：与旧的低饱和大圆角风格不兼容；旧调用需保留 primary 兼容参数。
### D50 开发目录来源

- 选择：--dev-extension 与 DEV_EXTENSION_ADD/REMOVE 把开发目录交给宿主作为独立来源 dev；只挂载、不复制、不写 disabled，列表 origin=dev；路径写 config.dev_extensions。
- 理由：开发迭代要即时生效且不能污染安装态；宿主扫描来源扩展即可复用激活链路。
- 代价：dev 与安装同 id 时仅本次会话覆盖；重启后以配置中的目录再次加载。

### D51 debugpy attach

- 选择：--debug 时宿主命令改为 python -m debugpy --listen 127.0.0.1:5678 --wait-for-client -m obox.extensions.host；仓库提供 .vscode/launch.json 的 attach 与 launch 配置。
- 理由：宿主独立进程，attach 不影响主 UI；debugpy 只在开发依赖，发布包不带。
- 代价：等待 attach 时扩展尚未激活，需先连调试器；--no-debug-wait 可跳过。

### D52 开发目录热重载

- 选择：QFileSystemWatcher 监听 dev 目录，去抖 400ms 后重启宿主；--no-dev-reload 关闭。
- 理由：复用已有的目录变化重启链路，不新增增量加载；保存即生效。
- 代价：断点调试时保存会重启宿主、打断会话。
### D56 扩展 API 命名空间

- 选择：按 VS Code 组织 window/workspace/commands/env/extensions/storage/network/message/log，函数与参数 camelCase；所有函数首参是只读 OboxContext。
- 理由：降低迁移成本；ctx 标识扩展与窗口，宿主可校验来源；UI 类在主进程，网络/存储/扩展信息在宿主。
- 代价：API 面变大，需按命名空间维护文档与测试。

### D57 网络代理与多协议

- 选择：设置页统一配置代理（enabled/proxyUrl/sslStrict/noProxy），network 默认读取；调用只保留 noProxy。HTTP/HTTPS 用 QtNetwork，TCP/SSH/SFTP 走 SOCKS5/HTTP CONNECT，UDP/QUIC 走 SOCKS5 UDP associate，ICMP 调系统 ping 且不支持代理，QUIC 用 aioquic。
- 理由：代理策略集中，扩展不接触网络栈；协议能力差异显式报错。
- 代价：UDP/QUIC 依赖代理服务端能力；ICMP 在代理下不可用。
### D58 程序目录由 exe 路径推导

- 选择：安装态 program_dir 取 sys.executable 的父目录；文件名是 python.exe/pythonw.exe/python3*.exe 时按源码态用仓库根；OBOX_PROGRAM_DIR 仍优先。
- 理由：Nuitka 冻结后 __file__ 与 __compiled__ 在不同模块里不可靠，exe 路径稳定。
- 代价：绿色版改名 python.exe 时需用环境变量覆盖。
