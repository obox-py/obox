---
status: done
---

# 设置与多语言 Spec Delta

## Purpose

设置页缺开机自启动；托盘与关闭询问的文案绕过 i18n；语言下拉列了上百种 locale 却没有对应文案，配置里存的还是地区标签；浅色正文被感知为灰；扩展失败只显示「失败」二字。本变更把这些拉回基线承诺的可观测行为。

## ADDED Requirements

### Requirement: 开机自启动

设置页「行为」分类 SHALL 提供「开机自启动」开关，默认关闭；打开时在 HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run 写入指向当前可执行文件的键值，关闭时删除该键值；修改即时生效并持久化到 settings.obox.autostart；以源码方式运行（非打包）时开关为禁用态并说明仅安装版可用。

#### Scenario: 打开自启动

- **WHEN** 在设置 → 行为 打开开机自启动
- **THEN** 注册表 Run 键出现 obox 项，值为当前 obox.exe 绝对路径，配置里 settings.obox.autostart 为 true

#### Scenario: 关闭自启动

- **WHEN** 再次关闭该开关
- **THEN** Run 键被删除，配置为 false，重启后不再随系统启动

#### Scenario: 源码运行不可用

- **WHEN** 用 uv run obox 启动后打开设置 → 行为
- **THEN** 开关禁用并显示「仅安装版可用」

### Requirement: 界面文案多语言覆盖

obox 自身与随安装包分发的扩展（app、settings、management、gallery、demo、chartdemo、pickerdemo、webapp、rdp）SHALL 为设置中列出的每种语言提供完整文案；托盘菜单、关闭询问对话框、toast、扩展管理页与运行期错误通知的文案 SHALL 来自各自 i18n.json，不得硬编码单一语言；扩展传给宿主的文案（视图数据、侧栏标题、对话框与 app 卡片标题）里的 i18n 占位符 SHALL 由宿主按该扩展的命名空间替换，扩展不需要自备翻译表；设置的语言下拉 SHALL 只列出文案齐全的语言（本次为 zh-CN、zh-HK、zh-TW、en-US），新增语言必须整套文案齐全才入列。

#### Scenario: 英文下的托盘与关闭框

- **WHEN** 语言切到 en-US 后右键托盘并关闭窗口
- **THEN** 菜单项与关闭询问按钮均为英文

#### Scenario: 四种语言全覆盖

- **WHEN** 依次切换 zh-CN、zh-HK、zh-TW、en-US
- **THEN** 设置页、托盘、关闭框、扩展管理页与已装扩展界面没有硬编码中文残留，全部随语言变化

#### Scenario: 清单外的语言不入列

- **WHEN** 打开设置的语言下拉
- **THEN** 只出现四个选项，不出现没有完整文案的 locale

#### Scenario: 扩展数据文案随语言切换

- **WHEN** management 扩展把条目状态写成 i18n 占位符并随视图数据下发，当前语言为 en-US
- **THEN** 界面显示 Active 而不是占位符原文或中文

## MODIFIED Requirements

### Requirement: 主题色板与文字层级

两套套件 SHALL 各自提供低饱和色板：背景、表面、次级文字、分割线与强调色，强调色饱和度明显低于高饱和蓝，大面积背景不出现纯黑与纯白；文字层级只用字号与文字色阶区分；light 套件的主文本（正文、标题、设置项标题、列表项、输入内容）为纯黑 #000000，说明与禁用态保留灰阶。

改自基线 spec.md:522「主题色板与文字层级」；冲突点：基线场景要求「正文是中深灰」。

#### Scenario: light 主文本为纯黑

- **WHEN** 以 light 套件打开主界面与设置页
- **THEN** 标题、设置项标题、列表项与输入内容为 #000000，说明文字仍为灰阶

#### Scenario: dark 不受影响

- **WHEN** 切到 dark 套件
- **THEN** 文字色阶与基线一致

### Requirement: 设置读写

设置扩展 SHALL 通过 SETTINGS_SET 提交修改；obox SHALL 把值写入 .obox/config.json 的 settings 段（键为 扩展标识.属性名），并对主题与语言立即应用；写入失败时保留旧值并回报错误；语言一律以 BCP-47 码存储（顶层 language 与 settings.obox.language 都是码，不是地区标签），启动时把旧配置里的地区标签一次性映射成码并写回。

改自基线 spec.md:892「设置读写」；冲突点：基线只写「值」，未规定语言的存储形态。

#### Scenario: 立即生效

- **WHEN** 把语言改成 en-US
- **THEN** 界面切换为英文，顶层 language 与 settings.obox.language 都是 en-US

#### Scenario: 旧标签迁移

- **WHEN** 旧配置里 language 为「中国大陆」
- **THEN** 启动后按 zh-CN 运行，配置写回 zh-CN

### Requirement: 设置扩展

工程 SHALL 提供系统扩展 extensions/settings：只注册 sidebar 视图；界面仿 VSCode，左侧分类（行为、外观、语言、扩展、关于）、右侧设置项、顶部搜索；外观、语言与行为修改即时生效。

改自基线 spec.md:836「设置扩展」；原为四个分类且未含行为。

#### Scenario: 分类与设置项

- **WHEN** 打开设置页
- **THEN** 左侧出现五个分类，行为分类含关闭行为与开机自启动两项

### Requirement: 扩展故障隔离

单个扩展激活失败 SHALL 不阻断其他扩展激活；宿主进程异常退出后，obox 重启宿主并恢复扩展；激活失败的原因 SHALL 在扩展管理页该条目上可见，通知里带扩展名与原因，不得只显示「失败」。

改自基线 spec.md:908「扩展故障隔离」；冲突点：基线已要求提示失败原因，实现只给扩展名。

#### Scenario: 某个扩展激活抛异常

- **WHEN** rdp.chenzhi 因缺少运行期文件在导入时抛异常
- **THEN** 其它扩展照常激活，管理页该条显示原因（如「找不到 fields.py」），通知带同样内容

### Requirement: 扩展打包产物

工程 SHALL 提供一条命令，分析指定扩展目录内的 import 图，把入口与关联的本地 Python 文件各自编译为同名 pyd，与 extension.json、i18n.json、assets 与 views 一起打成 zip，产物为 dist/名称.作者.{版本}.oix；扩展的运行期依赖 SHALL 全部落在 import 图内或随包分发的静态文件里，不得在运行期读取未随包分发的源码文件。

改自基线 spec.md:709「扩展打包产物」；冲突点：基线只规定 import 图内的文件，未禁止运行期读取目录外的其它源码文件，rdp.chenzhi 因此缺 fields.py 而无法激活。

#### Scenario: 运行期依赖随包

- **WHEN** 打包 rdp.chenzhi 并解压安装
- **THEN** 安装目录里只有 pyd 与静态文件、没有 .py，扩展仍能激活

#### Scenario: 正常打包

- **WHEN** 对包含 extension.json 与 extension.py 的目录执行打包命令
- **THEN** dist 下出现 名称.作者.{版本}.oix，zip 根目录含 extension.json、extension.pyd、i18n.json（若有）与 assets/、views/

## Impact

- spec.md:522 场景由「正文中深灰」改为「主文本纯黑」，dark 不受影响；以 TEXT_MUTED 呈现的说明文字保持灰阶。
- spec.md:786-827 语言下拉从全量 locale 改为固定四项，属于能力边界收窄；旧配置标签启动时迁移，已装扩展不用重装。
- spec.md:836 设置扩展分类由四个变五个，补上代码里已有的行为分类。
- spec.md:892 语言存储形态明确为 BCP-47 码，兼容旧配置。
- spec.md:908 失败提示从扩展名补到「名 + 原因」，隔离与重启语义不变。
- spec.md:709 打包产物补上「运行期依赖必须随包」的约束，rdp.chenzhi 的 oix 内容随之变化（fields.pyd 入包）。
