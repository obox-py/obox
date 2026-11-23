---
status: done
---

# App 扩展 Delta Design

## Scope

模板引擎（表达式、指令、局部更新）、视图数据与生命周期、应用清单与元数据、App 系统扩展、应用窗口与持久化。

## Context

主窗口已有 rail + 视图栈与自绘标题栏；扩展通过清单声明 views，语言与 oml 通路已就绪。本轮加入应用注册点、应用网格页、独立窗体与窗口复用。

## Changes

| 模块 | 改动 | 需求 |
|---|---|---|
| obox/api/app.py | 新增 APP_LAUNCH_MSG、APP_OPEN_MSG 与 APP_UI_MSG 消息 | 打开应用与窗口复用 |
| theme/*/components/appgrid.py | 新增 AppGrid 组件：应用卡片网格，数据由外部注入，点击发 open 事件 | 应用页作为系统扩展 |
| extensions/app | 新增系统扩展：清单、视图、i18n、转发开窗 | 应用页作为系统扩展 |
| obox/extensions/manifest.py | 解析 contributes.app 为应用清单（对象或数组），校验 id/图标/开关 | 应用注册 |
| obox/extensions/host.py | 激活结果带应用清单与图标绝对路径 | 应用网格 |
| obox/ui/app_window.py | 独立窗体，支持隐藏复用（persistent）与内容替换 | 打开应用与窗口复用 |
| obox/app.py | 应用页装配、卡片事件、开窗消息、UI 回传渲染、超时 | 三条需求 |
| theme/*/components/image.py | Image 组件，按路径原样显示 | 应用网格 |
| theme/*/components/container.py | Text 支持 size | 应用网格 |
| extensions/demo | 声明两个应用之一、处理打开消息、新增 views/app.oml | 打开应用与窗口复用 |

## 应用搜索

| 模块 | 改动 |
|---|---|
| obox/api/app.py | 新增 APP_LIST_MSG 与 APP_VIEW_DATA_MSG |
| obox/app.py | 应用就绪后把完整列表推给 app.obox；收到过滤结果时校验 owner 与已知 id，再更新视图 apps |
| extensions/app/extension.py | 缓存列表、按标题/描述/作者做大小写不敏感子串过滤、回注结果 |
| extensions/app/views/main.oml | 网格上方加搜索框，空查询显示全部 |
| extensions/app/i18n.json | 搜索框占位文案 |
| obox/app.py | 用 QFileSystemWatcher 监听 extensions 与 .obox/extensions，变更后去抖 400ms 重启扩展宿主 |
| obox/extensions/supervisor.py | 新增 restart()：停掉宿主进程再启动，触发重新激活与 payload 推送 |

## 模板引擎

| 模块 | 改动 |
|---|---|
| obox/ui/expr.py | 新增：表达式求值（路径、length、字面量、比较、!），未知返回 None |
| obox/ui/template.py | 新增：编译节点，处理 o-for/o-if 与绑定，产出可局部更新的视图句柄 |
| obox/ui/builder.py | 修改：接受作用域与数据，装配时记录绑定与区域 |
| obox/app.py | 修改：视图数据注入与 set_data，生命周期事件 |
| obox/api/lifecycle.py | 新增：mounted/updated/unmounted 消息 |

## 决策

- 应用清单在激活时算好并随 payload 下发，obox 不再读扩展文件。
- 图标解析：assets/相对路径 resolve 后必须落在 assets 内，否则退回扩展图标。
- 窗口注册表按 app_id 索引；single 为 true 时复用，persistent 为 true 时 close 仅 hide。
- 语言切换：关闭所有应用窗口（含持久化窗口）后按新语言重新请求。
- 内联片段与 oml 共用装配通路，仅来源不同。

## Baseline Diff

| 基线文件 | 章节 | 变为什么 |
|---|---|---|
| codespec/specs/spec.md | 新增模板指令、视图数据、生命周期、应用注册、应用页、应用网格、打开应用 | 追加七条需求 |
| codespec/specs/design.md | D18、D19 | 模板局部更新与应用窗口复用 |
| docs/arch.md | 4.1 模块表、4.3 决策表 | 补模板引擎与应用页 |
| README.md | 模板指令与应用扩展 | 用法说明 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| 扩展不响应打开消息 | 3 秒超时提示 |
| oml 越界或缺失 | load_oml 校验，失败在窗体内提示 |
| 持久化窗口泄漏 | 关闭窗口对象随主窗口销毁一并释放 |
