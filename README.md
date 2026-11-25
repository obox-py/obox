# obox

obox 是一个基于 PySide6 的可扩展桌面程序（控件全部为纯 Qt 与自绘，不依赖第三方组件库）：界面用 HTML 组件声明、QSS 定样式、消息驱动行为，功能通过 extensions 目录下的扩展按 VSCode 的方式装配进来。

## 目录

- [简介](#简介)
- [功能特点](#功能特点)
- [技术栈](#技术栈)
- [环境要求](#环境要求)
- [安装](#安装)
- [快速开始](#快速开始)
- [目录结构](#目录结构)
- [扩展开发](#扩展开发)
- [路线图](#路线图)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 简介

obox 面向需要「桌面外壳 + 第三方功能扩展」的场景：主程序提供窗口、导航、主题与消息通道，扩展只写 Python 与静态资产即可贡献界面与命令。

- 适用场景：内部工具平台、需要插件化的桌面客户端、教学与被集成的演示程序
- 不适用场景：纯命令行工具、需要用 Web 技术栈渲染复杂页面的产品
- 当前状态：地基阶段，界面框架、消息通道与扩展系统按 codespec 中的变更推进

## 功能特点

- **HTML 组件 DSL**：扩展用 PascalCase 标签描述界面，obox 解析后按当前主题套件装配为原生控件；界面里写 `on_click` 这类属性即声明事件订阅，没写就不会收到消息
- **消息驱动的组件交互**：组件以 id 标识，事件、状态查询与状态修改统一走消息，扩展不必直接持有控件对象
- **无端口的进程通道**：obox 与扩展宿主通过本地命名管道通信，帧为长度前缀加 JSON，适配 Windows 且不监听任何网络端口
- **仿 VSCode 的扩展体系**：extension.json 声明清单与注册点，extension.py 提供 activate 与 deactivate，context 注入扩展所需能力
- **可等待的请求应答**：请求支持带超时的阻塞等待、回调与 await 三种取结果方式
- **可替换的主题套件**：light 与 dark 各自是独立的组件实现，编译为 pyd 放在 `.theme/`；启动按配置加载，缺省 light，运行中可切换
- **自绘标题栏**：无边框窗口配自绘标题栏，支持拖动、双击最大化、边缘缩放与右键系统菜单，Windows 上带系统阴影

## 技术栈

| 类别 | 选型 | 说明 |
|---|---|---|
| 语言 | Python 3.12 | 与 .python-version 一致 |
| GUI 框架 | PySide6 | Qt for Python，主程序与扩展宿主都依赖 |
| 组件实现 | 纯 Qt 控件与自绘 | 按钮、输入、选择、页签、开关等都由套件自己实现 |
| 界面描述 | 自研 HTML 组件 DSL 与 QSS | 无 Web 引擎，标签映射到原生组件 |
| 进程通信 | QLocalServer 与 QLocalSocket | Windows 上即命名管道 |
| 打包 | Nuitka | 把 theme 套件编译为 pyd |
| 测试 | pytest 与 pytest-qt | 组件装配、消息编解码与扩展生命周期 |

## 环境要求

| 依赖 | 版本要求 | 说明 |
|---|---|---|
| Python | 3.12 及以上 | 与 pyproject.toml 一致 |
| PySide6 | 6.6 及以上 | 含 QtCore 与 QtWidgets |
| 操作系统 | Windows 10 及以上 | 当前只验收 Windows，代码保持跨平台写法 |

## 安装

```bash
git clone https://example.com/obox.git
cd obox
uv sync                                 # 建 .venv、装 PySide6、可编辑安装 obox
uv run python scripts/build_theme.py    # 编译主题套件，产出 .theme/light 与 .theme/dark
```

验证安装：

```bash
uv run obox --version
# 期望输出：obox 1.0.0
```

## 快速开始

```bash
uv run obox
```

主程序启动后自动扫描 extensions 目录、拉起扩展宿主进程，并把已激活扩展声明的视图挂到主窗口容器里：主区域进内容栈，侧栏只放扩展图标，底部栏放声明到底部容器的组件。

界面自检（无需人工点）：

```bash
python scripts/verify_ui.py
# 截图写入 tmp/pics，日志写入 tmp/logs，失败时退出码非 0
```

## 主题套件

界面外观由两套独立实现的组件库提供，源码在 theme/light 与 theme/dark，编译后放 .theme/{名称}/：

```bash
uv run python scripts/build_theme.py            # 两套都编
uv run python scripts/build_theme.py dark       # 只编 dark
uv run obox --theme dark                        # 临时用 dark 启动
```

启动时 obox 扫描 .theme 下的套件，按 .obox/config.json 的 theme 字段选一套（缺省 light）；缺 pyd 或清单直接报错退出。设置界面里的切换留待后续版本，当前用配置或命令行参数。

视觉取向：低饱和配色、默认不描边、控件圆角 10、卡片 16、视图边距 20、组件间距 16、控件高 38；light 走暖白纸感，dark 走深中性灰。间距与色板都由套件提供，换套件即换节奏。

字体：每套套件自带 HarmonyOS_Sans_SC.ttf（放在 theme/{name}/fonts，构建时复制到 .theme/{name}/fonts），启动时注册，不依赖系统安装；字体许可见同目录 LICENSE.txt。

```json
{ "theme": "dark" }
```

## 目录结构

```text
obox/
├── obox/                     # 主程序包
│   ├── main.py               # 入口
│   ├── app.py                # 应用启动与主窗口装配
│   ├── api/                  # 消息基类、组件消息三件套、请求对象
│   ├── core/                 # 消息总线与命名管道（ipc/）
│   ├── ui/                   # 解析、装配、注册表、套件加载与主窗口
│   ├── extensions/           # 清单校验、扫描、宿主进程与管理器
│   └── assets/               # 主程序图标
├── theme/                    # 主题套件源码
│   ├── light/               # 浅色组件实现与主题
│   └── dark/                # 深色组件实现与主题
├── .theme/                   # 编译产物：{名称}/{名称}.pyd 与 theme.json
├── extensions/               # 扩展开发目录，一个子目录一个扩展
│   ├── demo/                 # 示范扩展
│   └── gallery/              # 组件画廊：一页展示全部组件与 Flex
├── dist/                     # 打包产物：名称.作者.{版本}.oix
├── .obox/extensions/         # 已安装扩展（.oix 解包后的目录）
│       ├── extension.json
│       ├── extension.py
│       └── assets/
├── tests/                    # 契约层、运行层、表示层与端到端测试
├── scripts/                  # 构建与验证脚本（build_theme.py、verify_ui.py）
├── codespec/                 # 规格基线、变更与任务文档
├── docs/                     # 架构文档
├── pyproject.toml
└── README.md
```

## 扩展开发

一个扩展就是一个目录：

1. 在 extensions 下新建目录，例如 extensions/hello
2. 写 extension.json：名称、版本、作者、描述、入口、图标与注册点
3. 写 extension.py，提供 activate 与 deactivate 两个函数，接收注入的 context
4. 把 svg 图标与 QSS 放进同目录的 assets
5. 需要界面时，声明视图并给出 HTML 组件片段；需要事件的组件写上 on_click、on_input 这类属性，没写的交互不会产生消息
6. 图标用 svg：侧栏的扩展图标会按主题色重染成单色、选中变色，因此画轮廓比堆颜色更好看；obox 自身图标保持原色，不重染
6. 需要横向或流式排布时用 Flex 容器：direction、wrap、justify、align、gap，子项可写 grow 占满剩余空间

## Agent 技能

`.agents/skills` 下有四个技能，agent 按触发词直接使用：

| 技能 | 用途 | 一键命令 |
|---|---|---|
| obox-ext-dev | 写扩展：清单、context、oml、i18n、应用、打包 | `.agents/skills/obox-ext-dev/scripts/scaffold_extension.py` |
| obox-theme-dev | 写主题套件与组件、构建 pyd | `.agents/skills/obox-theme-dev/scripts/check_theme.py` |
| obox-ui-test | 界面验证、截图与断言 | `.agents/skills/obox-ui-test/scripts/run_verify.py` |
| obox-test | 单测、静态检查与基线校验 | `.agents/skills/obox-test/scripts/check_all.py` |

每个技能目录含 SKILL.md 与按需的 references、templates、scripts；脚本用 uv 在仓库根运行。

## 远端仓库与 CI

- 组织 obox-py 下三个仓库：obox（主程序、系统扩展、系统主题）、rdp、webapp（用户扩展各一仓）。
- PR 上运行 pytest 与打包冒烟；打 v* tag 触发 Release，产物为 obox 的 x86_64 / arm64 安装包，以及 rdp、webapp 对应架构的 oix。

## 安装包

```bash
uv run python scripts/build_exe.py                 # Nuitka standalone → build/obox.dist/obox.exe
uv run python scripts/build_installer.py           # NSIS → dist/obox-{version}-setup.exe（唯一安装包）
```

安装包只有一个，运行后先选范围（所有用户 / 仅为我安装），再在目录页改路径：所有用户默认 `Program Files\obox` 且需要管理员，当前用户默认 `%LOCALAPPDATA%\Programs\obox` 且不需要提权。

安装目录：obox.exe 与运行时文件、`.theme/{light,dark}`、`extensions/{app,settings}`（已解压的系统扩展）。用户数据始终在 `%LOCALAPPDATA%\obox`（config.json、扩展存储、用户安装的 .oix），卸载不删。

静默安装：`obox-1.0.0-setup.exe /S /CURRENTUSER /D=目标目录`（或 `/ALLUSERS`）。卸载会删除程序文件、快捷方式与对应范围的注册表项，保留 `%LOCALAPPDATA%\obox` 下的用户数据。

需要 NSIS（makensis）；构建脚本会自动先编 exe 与主题，缺 makensis 时提示安装方式。

## 托盘与关闭

同一 Windows 用户只运行一个 obox 实例；再次启动会唤醒已有窗口。关闭窗口默认询问：最小化到托盘 / 退出 / 取消，勾选「记住我的选择」后不再询问。设置 → 行为 可改关闭行为（每次询问 / 最小化到托盘 / 直接退出）。托盘右键菜单提供显示主窗口、设置与退出。

## 设置

设置是系统扩展 extensions/settings（settings/obox/1.0.0），只注册 sidebar 视图：左侧分类（外观、语言、扩展、关于）、右侧设置项、顶部搜索。主题与语言修改即时生效并写入 `.obox/config.json` 的 settings 段；扩展可在清单里用 contributes.configuration 贡献 bool/string/enum 设置项，会自动出现在「扩展」分类。

## 模板指令与应用扩展

OML 支持 o-for、o-if 与值绑定：

卡片用 o-for 遍历列表，id 与 value 用双花括号包住 `app.id` 绑定，标题用 `app.title` 绑定；
`o-for="item in items"` 的作用域里可用 `item` 与 `index`，`o-if` 控制是否渲染。

- `o-for="item in items"` 重复元素，作用域里可用 `item` 与 `index`；`o-if="expr"` 控制是否渲染
- 表达式支持点路径、`.length`、字面量以及 `==`、`!=`、`>`、`<`、`!`；解析不了的引用原样保留
- 视图数据来自 `register_view(..., data={...})`，obox 也能注入或更新；更新时只改绑定文本、重建指令区域
- 视图挂载与销毁会向扩展发 `VIEW_MOUNTED_MSG` / `VIEW_UNMOUNTED_MSG`

应用扩展：扩展在 `extension.json` 里声明 `contributes.app`，侧栏「应用」页（extensions/app 系统扩展）会用网格列出；点卡片后 obox 发 `APP_OPEN_MSG`，扩展回 `APP_UI_MSG` 在独立窗口渲染。`single`/`persistent` 控制窗口复用与关闭保留；应用页顶部有搜索框，按标题/描述/作者做子串过滤，扩展增删后列表自动同步。

## 多语言与 OML

视图可以写成 `.oml` 文件（obox 组件语法），注册时给相对扩展目录的路径，而不是把整段文本传过去：

```python
context.register_view("demo.main", "views/main.oml", "main", "示范")
```

文案通过 i18n 注册，oml 里用 `i18n 引用（双花括号包住 i18n 与条目 id）` 引用：

```python
context.register_i18n("title", {"zh-CN": "示范扩展", "en-US": "Demo extension"})
```

在 oml 的属性值里写双花括号包住的 `i18n.title`，渲染时会替换成当前语言的文案。

- name 是扩展标识 `名称.作者`；obox 主窗体用 `obox` 注册，扩展只能注册自己的 name
- values 必须以 BCP-47 为 key，且必须提供 `zh-CN`；缺当前语言时回退 zh-CN，未注册的引用原样保留
- 语言可在标题栏右侧的语言按钮里手动切换，切换后视图与外壳文案立即重建，选择写入 `.obox/config.json`
- 启动时也可用 `uv run obox --lang en-US` 覆盖，缺省 `zh-CN`

## 扩展打包与安装

开发完成后可以打包成单一文件分发：

```bash
uv run python scripts/pack_extension.py extensions/gallery
# 产物：dist/gallery.obox.0.1.0.oix
```

打包会把入口与扩展目录内的关联 py 逐个编译为同名 pyd，与 extension.json、assets、views/、i18n.json 一起打 zip；obox.api 与第三方库不打进去，运行时共用环境。

安装：把 .oix 放进 .obox/extensions，启动时自动解压到 .obox/extensions/名称.作者 并加载 extension.pyd。加载顺序为先安装目录、后 extensions/ 源码目录；同名扩展以安装版为准并记录告警。

扩展标识由「名称.作者」组成，消息的 src 与 dst 都使用这个格式，dst 为空表示广播。

## 路线图

- [x] 建立工程脚手架与规格基线
- [x] 界面框架：HTML 组件 DSL、21 个组件标签（含 Flex、卡片、选择容器、提醒条、图片、导航项）、QSS 主题
- [x] 消息层：组件消息三件套、请求应答与异步等待
- [x] 进程通道：命名管道服务端与客户端
- [x] 扩展系统：清单扫描、宿主进程、context 与注册点
- [x] 示范扩展与端到端演示（测试与截图验证脚本）

## 贡献指南

1. 从 master 拉分支，改动前先读 codespec/specs 与 docs/arch.md
2. 提交前跑 pytest 与 ruff check
3. 提交信息使用 Conventional Commits

## 许可证

主程序代码按仓库根目录的许可证文件发布；运行时只依赖 PySide6（LGPL）与 Qt，无第三方组件库的授权约束。

## 鸣谢

- PySide6：Qt for Python 绑定
- Ant Design：组件语义与交互的参照