---
status: done
---

# 远程桌面与网页应用 Spec Delta

## Purpose

在 Python obox 里新增两个用户扩展：RDP 连接管理与网页应用启动器；同时补上「扩展读取自己配置」的通道，让 webapp 的选项在设置页可配、扩展里可读。

## ADDED Requirements

### Requirement: 远程桌面扩展

工程 SHALL 提供用户扩展 rdp.chenzhi：contributes.app 提供「远程桌面」卡片，打开后在 App 窗口里显示连接列表（顶部搜索、右上新建）。连接字段为名称、主机、端口、用户名、域、记住密码；名称必填且在列表内唯一，主机必填，端口取 1–65535，缺省 3389。打开连接时生成 .rdp 文件，记住密码时把 DPAPI 密文写进 .rdp 的 password 51:b 字段（不经过命令行），再以脱离 obox 进程树的方式启动 mstsc.exe；obox 退出不影响已打开的会话。勾选记住密码时用 Windows DPAPI 加密保存，未勾选不写盘；解密失败提示重新输入。非 Windows 平台打开时提示仅支持 Windows。

#### Scenario: 新建与编辑走模态框

- **WHEN** 点「新建连接」或某条连接的「编辑」
- **THEN** 弹出模态框承载表单，保存或取消后关闭

#### Scenario: 新建并打开连接

- **WHEN** 填入名称「办公机」、主机 10.0.0.8、用户名 chenzhi、勾选记住密码并点打开
- **THEN** 生成 .rdp 与加密密码，mstsc 以独立进程启动，列表里出现该连接

#### Scenario: 编辑回填

- **WHEN** 点某条连接的「编辑」
- **THEN** 表单按数据绑定回填该连接的全部字段（含显示、连接、音频、本地资源、体验各组）

#### Scenario: 名称重复被拒

- **WHEN** 新建连接的名称与已有连接相同
- **THEN** 保存被拒绝并提示名称已存在

#### Scenario: mstsc 不认密文
- **WHEN** .rdp 里的 password 51:b 无法被 mstsc 解密
- **THEN** 连接仍启动，由系统提示输入密码，页面记录该次降级

#### Scenario: 不记住密码

- **WHEN** 不勾选记住密码
- **THEN** 磁盘上不出现该连接的密码密文，打开时由系统提示输入

### Requirement: 网页应用扩展

工程 SHALL 提供用户扩展 webapp.chenzhi：contributes.app 提供「网页应用」卡片，打开后显示站点列表（搜索、新建）。站点字段为名称、URL、忽略证书错误；名称必填唯一，URL 必填且只接受 http/https。打开站点时用 Chrome 的 --app 模式（参数值就是站点 URL）与独立的 `--user-data-dir` 启动，配置文件目录位于配置的 profile 根下、按条目区分；勾选忽略证书错误时追加 `--ignore-certificate-errors`；进程脱离 obox。找不到 Chrome 时在页面提示。扩展配置包含 profile 根目录（属性名 profileroot，设置键 webapp.chenzhi.profileroot，默认空表示 storage/profiles）与单站点数据上限（属性名 limitmb，枚举 0/512/1024/2048，默认 2048），宿主在激活后与配置变更时下发；单个站点的 profile 目录超过上限时拒绝打开并提示清理缓存。

#### Scenario: 站点表单走模态框

- **WHEN** 点「新建站点」或某条站点的「编辑」
- **THEN** 弹出模态框承载表单，保存或取消后关闭

#### Scenario: 打开站点

- **WHEN** 条目名称「工单」、URL https://tickets.local、勾选忽略证书错误
- **THEN** Chrome 以应用模式启动，使用该条目独立 profile，且带忽略证书参数

#### Scenario: 编辑回填站点

- **WHEN** 点某条站点的「编辑」
- **THEN** 表单回填名称、网址、说明、窗口尺寸/位置、语言、缩放、忽略证书与 GPU 选项

#### Scenario: 找不到 Chrome

- **WHEN** 机器上没有 Chrome
- **THEN** 页面提示未找到 Chrome，不启动任何进程

#### Scenario: 超出数据上限被拦
- **WHEN** 某站点的 profile 目录超过配置的上限
- **THEN** 打开被拒绝，页面提示清理缓存，且不启动 Chrome

#### Scenario: 配置生效

- **WHEN** 在设置页把 profile 根目录改到另一个盘
- **THEN** 扩展收到新配置，之后打开的站点使用新根下的 profile

## MODIFIED Requirements

### Requirement: 扩展配置贡献

改自基线「扩展配置贡献」：补扩展读取自己配置的通道。

extension.json SHALL 支持 contributes.configuration（属性表每项声明 type、title、default 与可选 enum），类型仍为 bool、string、enum；obox 校验后汇总成设置项下发；宿主 SHALL 在扩展激活后与配置变更时，把该扩展的配置当前值（键、值、默认值）下发给扩展；未设置的键返回 default，非法值被拒绝并保留旧值。

#### Scenario: 激活时收到配置

- **WHEN** webapp 扩展激活且设置页里 profile 根目录为空
- **THEN** 扩展收到该键的默认值，用它作为 profile 根

#### Scenario: 变更后再下发

- **WHEN** 在设置页修改单站点数据上限
- **THEN** 扩展收到新值，不需要重启

### Requirement: 扩展开发技能

改自基线「扩展开发技能」：补 App 卡片与配置读取示例。

工程 SHALL 提供 .agents/skills/obox-ext-dev，references 覆盖清单、context API、oml、i18n、打包，并在清单示例里给出 contributes.app 与 contributes.configuration 的写法、在 context API 里说明配置下发的消息与字段。

#### Scenario: 脚手架包含 App 与配置

- **WHEN** 用脚手架生成扩展
- **THEN** 生成的清单可声明 app 与 configuration，文档给出读取配置的示例

## Impact

- 新增两条宿主到扩展的消息路径：配置下发（激活与变更各一次）
- 新增两个源码扩展目录与 App 卡片；扩展 id 为 rdp.chenzhi 与 webapp.chenzhi
- 设置页会多出「网页应用」的扩展配置项
- 依赖 Windows 能力（DPAPI、cmdkey、mstsc、Chrome），非 Windows 只提示不执行