---
status: done
---

# 扩展管理 Design Delta

受影响的组件、依赖方向与流程时序由 df-arch 画在 delta-arch.md。本文件只写这次改哪里、为什么这么改、基线会怎么变。

## Context

现状是「启动时一次性激活」：宿主在 activate_all 里解压 .oix、扫描三个根、逐个 activate，然后把 extensions/views/i18n/commands 一次性推给 obox（obox/extensions/host.py:81-118）；obox 收到 status 后整批挂载视图（obox/app.py 的 _on_extensions_ready）。这套流程没有运行中的增删入口，也没有管理页；用户装扩展只能手工放文件再重启。

本次要在此之上加三件事：宿主能被消息驱动做安装/卸载/启用停用、obox 能增量应用结果、并多一个系统扩展承载页面。

## Scope

- 扩展管理（ADDED）
- 扩展安装（MODIFIED）
- 扩展生命周期与上下文注入（MODIFIED）
- 扩展目录与清单（MODIFIED）

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| `obox/api/extensions.py`（新增） | 定义三条宿主控制消息（安装、卸载、启用/停用）与一条宿主回推（扩展变更），以及 obox 推给管理扩展的列表消息 | 扩展安装、扩展管理 |
| `obox/extensions/host.py` | 监听三条控制消息：安装走 staging 包解压并激活；卸载调 deactivate、摘注册点、删目录与存储；启用/停用同样摘除或重新激活；每个动作结束后回推变更列表 | 扩展安装、扩展生命周期与上下文注入 |
| `obox/extensions/loader.py` | 增加单包安装与卸载函数，供宿主在运行中调用；启动扫描仍只看安装根下的 .oix，忽略 staging 子目录 | 扩展安装 |
| `obox/app.py` | 管理页动作的编排：文件选择、复制到 staging、转发给宿主、应用宿主回推的增量（挂视图、摘视图、刷新应用与设置）、把禁用名单写进 config | 扩展安装、扩展目录与清单 |
| `obox/ui/main_window.py` | 新增 remove_view(view_id)，用于摘除被卸载扩展的视图；其余不变 | 扩展安装 |
| `obox/ui/confirm_dialog.py`（新增） | 卸载确认框：显示扩展 id 与将被删除的目录，确认/取消 | 扩展管理 |
| `extensions/management/`（新增） | 系统扩展本体：extension.json、extension.py、views/main.oml、i18n.json、main.svg；页面由安装按钮、搜索框、卡片列表与卡片内操作组成 | 扩展管理 |
| `tests/test_extension_manage.py`（新增） | 覆盖安装/卸载/启停的消息流转、增量应用、禁用名单持久化、管理扩展的过滤函数 | 全部 |

## Decisions

- 控制消息由宿主处理、obox 只编排：文件对话框与确认框在 obox，解压与模块加载在宿主，保持「宿主是扩展生命周期唯一持有者」的既有边界。
- 安装包先复制到 `.obox/extensions/incoming/` 再通知宿主：宿主只认安装根内的路径，避免它去访问任意用户路径；安装成功后删除该包，启动扫描忽略 incoming 目录。
- 宿主回推用一条「扩展变更」消息，带 removed 与 changed 两组 id 与新的视图列表；obox 按 id 差分应用，不重建整窗，保住当前页与滚动位置。
- 禁用名单存 `.obox/config.json` 的 `extensions.disabled`，宿主启动时读取并跳过激活；停用与启用都走同一条控制消息，宿主不改配置文件。
- 卸载只对用户安装的扩展开放：宿主按来源判断，非用户来源直接拒绝并回报原因；删除范围是安装目录与该扩展的存储目录。
- 管理页与 App 页同构：Flex + Card 卡片、顶部搜索、空查询显示全部；卡片操作按钮只在用户来源时渲染。
- 覆盖升级先解压到同根的临时目录，成功后替换；失败清理临时目录并保留旧版本。

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 按 delta-spec.md 的 1 条 ADDED 与 3 条 MODIFIED 合并；扩展安装一节补运行中安装与卸载，生命周期补停用与跳过，目录与清单补来源与禁用名单 |
| design.md | 新增 D33「运行中扩展控制消息与增量应用」、D34「管理页与卡片操作」、D35「禁用名单与卸载边界」 |
| docs/arch.md | 4.1 分层图里宿主与 obox 之间补控制消息；5.1 启动与激活补「运行中增删」的分支（图由 df-arch 落） |
| README.md | 能力清单补「扩展管理」，使用方式补安装/卸载/禁用三步 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| Python 无法真正卸载模块，卸载后同 id 重装可能命中旧模块缓存 | 重装时以新目录路径加载并换模块名，失败时记录；卸载不承诺模块级回收 |
| 增量摘视图时正在显示该视图 | 摘除前判断当前视图，命中则先切到扩展管理页再移除 |
| 宿主回推与 obox 之间的 id 对不齐（视图 id 改名） | 以扩展 id 为粒度摘除：宿主回推 removed 扩展 id，obox 按 owner 摘掉全部视图 |
| 安装包复制到 incoming 后宿主崩溃，残留文件 | 启动扫描忽略 incoming；每次安装前清空该目录 |
| 禁用系统扩展导致设置页缺失 | 宿主对非用户来源拒绝停用；管理页也不渲染按钮 |

回滚：控制消息与宿主处理可以整体回退到「只在启动时安装」，管理页目录单独删除不影响其它扩展；禁用名单只是 config 里一个数组，删掉即恢复全部激活。
