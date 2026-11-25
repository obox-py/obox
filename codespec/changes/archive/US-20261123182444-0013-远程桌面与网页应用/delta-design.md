---
status: done
---

# 远程桌面与网页应用 Design Delta

受影响的组件、依赖方向与流程时序由 df-arch 画在 delta-arch.md。本文件只写这次改哪里、为什么这么改、基线会怎么变。

## Context

两个扩展都是用户扩展（.oix 或源码目录），运行在扩展宿主进程，界面用 OML 在 AppWindow 渲染；与 obox 的交互只有消息。现有 API 没有「扩展读取自己配置」的通道：设置页会渲染 configuration，但值只留在 obox 侧，扩展拿不到。

Windows 能力（DPAPI、mstsc、Chrome）只能在扩展进程内调用；宿主不提供封装。

## Scope

- 远程桌面扩展（ADDED）
- 网页应用扩展（ADDED）
- 扩展配置贡献（MODIFIED）
- 扩展开发技能（MODIFIED）

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| `obox/api/settings.py` | 新增 EXTENSION_CONFIG_MSG 与构造函数：obox → 扩展，payload 为 {values, defaults} | 扩展配置贡献 |
| `obox/app.py` | 激活完成后与设置变更后下发配置；App 窗口装配时保留 ViewHandle，让扩展用 `app. 加窗口 id` 更新数据；扩展目录按 extensions 清单登记 | 扩展配置贡献、两个扩展 |
| `extensions/rdp/extension.json` | 清单：app 卡片「远程桌面」、activationEvents、入口 | 远程桌面扩展 |
| `extensions/rdp/extension.py` | 连接模型与校验、JSON 存储、DPAPI 加解密、.rdp 生成、脱离式启动 mstsc、消息处理 | 远程桌面扩展 |
| `extensions/rdp/views/main.oml` | 列表 + 搜索 + 新建/编辑表单 + 打开/删除 | 远程桌面扩展 |
| `extensions/rdp/i18n.json`、`assets/main.svg` | zh-CN/en-US 文案与图标 | 远程桌面扩展 |
| `extensions/webapp/extension.json` | 清单：app 卡片「网页应用」、configuration（profileRoot、limitMb） | 网页应用扩展、扩展配置贡献 |
| `extensions/webapp/extension.py` | 站点模型与校验、JSON 存储、Chrome 探测、app 模式启动、配置读取 | 网页应用扩展 |
| `extensions/webapp/views/main.oml` | 列表 + 搜索 + 新建/编辑表单 + 打开/删除 | 网页应用扩展 |
| `extensions/webapp/i18n.json`、`assets/main.svg` | zh-CN/en-US 文案与图标 | 网页应用扩展 |
| `tests/test_extensions_process.py` | 两个扩展的纯函数：校验、.rdp 文本、命令拼装、Chrome 探测、配置解析 | 两个扩展 |
| `tests/test_extension_config.py` | 配置下发：激活后收到、变更后再收到、只收自己的键 | 扩展配置贡献 |
| `scripts/verify_ui.py` | 打开两个 App 卡片并截图（不发起网络/远程连接） | 两个扩展 |
| `.agents/skills/obox-ext-dev` | 补 App 卡片与配置读取示例 | 扩展开发技能 |
| `obox/ui/components/input.py` | 给 Input 加 password 属性（密码掩码） | 远程桌面扩展 |

## Decisions

- RDP 参数对齐 web 版：46 个字段按「账号/显示/连接/音频/本地资源/体验」分组，保存在 connections.json，生成 .rdp 时逐项写入；webapp 条目补说明、额外 origin、窗口尺寸/位置、启动最大化、语言、缩放、禁用 GPU。
- 数据绑定：builder 现支持 value 与 checked 属性的绑定（走组件 state_accessors 的 setter），编辑时表单回填不再依赖重建。
- 界面用 AppWindow + OML：列表与搜索在页面里，新建/编辑用 Modal 承载表单（页面里放一个常驻 Modal，扩展用 COMPONENT_MODIFY_MSG 控制 visible；取消、Esc、遮罩关闭都收起）。
- 数据存扩展 storage：`connections.json` / `secrets.json` / `sites.json`；密码只在 `secrets.json` 存 DPAPI 密文的 base64。
- 密码写进 .rdp 的 `password 51:b` 字段而不是 cmdkey：避免密码出现在命令行与进程列表里，mstsc 能直接解密；未记住时不写该字段，由系统提示输入。
- 脱离式启动：Windows 上 subprocess.Popen 带 DETACHED_PROCESS 与 CREATE_NEW_PROCESS_GROUP，close_fds；mstsc 传 .rdp 路径，Chrome 传 --app 与 --user-data-dir。
- Chrome 探测顺序：注册表 App Paths 的 chrome.exe → Program Files 常见路径 → PATH；找不到时把原因写进页面状态文字。
- 配置下发：配置属性名只能是小写字母数字（宿主清单校验），设置键为「扩展标识.属性名」；obox 在 _on_extensions_ready 之后与设置写入之后各推一次，payload 的 values/defaults 以属性名为键。
- App 窗口的数据通道：宿主装配 App 页面时保留 ViewHandle，扩展发 `view_data_message(src, "app. 加窗口 id", data)` 即更新；否则只能整页重渲染，输入框会丢焦点。
- 扩展目录登记：宿主按 extensions 清单的 directory 记下每个扩展目录，App 页面才能按相对路径加载 views/main.oml。
- 非 Windows：所有系统调用前先判断平台，返回「仅支持 Windows」的状态文字，不抛异常。
- 错误明文展示：页面底部一行状态文字（与参考实现不同，不静默），失败原因直接可见。

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 按 delta-spec.md 的 2 条 ADDED 与 2 条 MODIFIED 合并；扩展配置贡献补配置下发 |
| design.md | 新增 D42「扩展读取自己配置的下发」、D43「Windows 系统能力的扩展内封装」 |
| docs/arch.md | 扩展与 obox 的消息里补配置下发；扩展目录清单补 rdp 与 webapp（图由 df-arch 落） |
| README.md | 能力清单补远程桌面与网页应用两个扩展 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| DPAPI 调用失败（非 Windows 或受限） | 捕获异常，按「不记住密码」处理并提示；不写半截密文 |
| .rdp 字段写错导致 mstsc 不认 | 只写已验证的键：full address、username、domain、authentication level、prompt for credentials、password 51 |
| Chrome 版本差异导致参数不认 | 只使用长期稳定的 --app、--user-data-dir、--ignore-certificate-errors |
| 扩展配置变更时机早于激活 | obox 在激活后再推一次，扩展以最后一条为准 |
| 密码文件被同用户其它进程读取 | DPAPI 同用户可解；文件权限限当前用户，注释里写明边界 |

回滚：删掉两个扩展目录与配置下发消息即可；设置页会随扩展消失自动去掉配置项。