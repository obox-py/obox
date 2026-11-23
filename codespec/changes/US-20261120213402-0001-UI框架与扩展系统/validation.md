---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 本次结论 |
|---|---|---|
| `codespec/specs/spec.md` | 是 | 无结构问题；一处契约缺项记为需上游修正（V8） |
| `codespec/specs/design.md` | 是 | 无问题 |
| `delta-spec.md` | 是 | 一条 ADDED（主界面三段布局），形态合法 |
| `delta-design.md` | 是 | 2 处补正后无问题（V1、V2） |
| `task.md` | 是 | 5 处补正后无问题（V1、V2、V3、V4、V5、V6、V7） |
| `delta-arch.md` | 是 | 无问题 |
| `README.md` | 是 | 无问题 |
| 第二轮 `delta-spec.md` | 是 | 9 条 ADDED 加 1 条 MODIFIED，形态合法；一条需求名含大写导致覆盖检查误判，已改名 |
| 第二轮 `delta-design.md`、`delta-arch.md`、`task.md` | 是 | 4 处补正后无问题（V9 到 V12） |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 严重 | `spec.md` 的 Requirement: QSS 样式作用域、`task.md` 的 T13 | 扩展 QSS 只写了「可在 assets 中提供」，没有定义 obox 何时、依据什么加载它，T13 只做过滤，实现后扩展样式永远不会生效 | spec.md：扩展可在 assets 中提供 QSS；task.md 的 T13 步骤只写「qss.py 解析规则块」 | 已修复 |
| V2 | 严重 | `spec.md` 的 Requirement: 扩展目录与清单、`task.md` 的 T14 | 原始需求要求扩展图标统一用 svg，清单校验只查路径不查后缀，实现会接受 png | task.md 的 T14 步骤 2 原文只写「icon 与 QSS 路径必须落在 assets 内」 | 已修复 |
| V3 | 一般 | `task.md` 的 T14 与全局约束 | 清单字段写 publisher，需求与消息 src 写「作者」，术语漂移且未说明 src 后缀取哪个字段 | task.md 的 T14 步骤 1 列 publisher；全局约束写 src 为 名称.作者 | 已修复 |
| V4 | 一般 | `task.md` 的 T11 行与覆盖检查 | T11 行对应需求只列装配与事件，覆盖检查却把状态查询与修改算给它 | task.md 的 T11 行与「覆盖检查」中状态查询、状态修改两行 | 已修复 |
| V5 | 一般 | `task.md` 的 T18 步骤 1 | 视图容器取值未枚举，挂载时没有允许值集合 | task.md 的 T18 步骤 1 原文只写「加导航与视图容器区」 | 已修复 |
| V6 | 建议 | `task.md` 的 T16 步骤 1 | activationEvents 只被清单校验，不参与调度，v1 实际全量激活，需要写明以免实现者误以为要做事件激活 | task.md 的 T16 步骤 1 原文未提 activationEvents | 已修复 |
| V7 | 建议 | `task.md` 的 T18 验收命令 | 命令用 bash 的 QT_QPA_PLATFORM 前缀写法，Windows 原生 shell 不可复制执行 | task.md 的 T18 验收命令原文为 QT_QPA_PLATFORM=offscreen python -m obox.main | 已修复 |
| V8 | 一般 | `codespec/specs/spec.md` 的 Requirement: 组件消息 | 基线 spec 没有写「组件消息三件套不可继承」这条约束，任务侧已实现，契约侧缺失 | proposal.md 的需求草案第 2 条与 task.md 的 T4 步骤 1 都有该约束 | 需上游修正 |
| V9 | 严重 | `task.md` 的任务清单 | 缺少「删除 obox/ui/components 并给 demo 补 on_ 属性」的任务；不删会两套实现并存，不补 demo 点击会失效 | 第二轮把组件迁到 theme 两套库，但任务表没有删除与迁移项 | 已修复 |
| V10 | 严重 | `delta-design.md` 的 app.py 行 | 运行中切换只写「销毁并重建视图」，重建所需的视图定义没有缓存来源 | 原文只写「切换时销毁视图、换 provider、重建视图」 | 已修复 |
| V11 | 一般 | `delta-arch.md` 的待修改模块与第 2 张时序图 | 仍以 obox/ui/components 为参与者，与新结构冲突 | 模块表写「新增 15 个组件」，时序图参与者写 obox/ui/components | 已修复 |
| V12 | 建议 | `task.md` 的 T32 步骤 | README 要求补说明但没给 .obox/config.json 的示例 | T32 步骤 2 原文只写「补构建命令、theme 选择与切换说明」 | 已修复 |

## 处理记录

- 第 1 轮：报告 8 项（严重 2 / 一般 4 / 建议 2），用户选择全部修复；已修 7 项（V1 到 V7），V8 属基线问题，记为需上游修正，本轮不动基线。
- 第 2 轮：重跑 check.py，delta-spec、delta-design、delta-arch、task、scope 均无严重项与一般项；复核改动点：task.md 的 T11、T13、T14、T16、T18 与 delta-design.md 的两行 Changes 都已更新，修复未引入占位符。收敛。
- 第 3 轮（第二轮追加）：报告 4 项（严重 2 / 一般 1 / 建议 1），用户选择全部修复；已补 T33（删除旧组件包与迁移 demo）、给 app.py 补视图定义缓存、改写 delta-arch 的模块描述与时序图参与者、给 T32 补配置示例。重跑 check.py 为 0 问题。

## 遗留

- V8：基线 spec.md 需补「组件消息不可继承」的约束，归基线补正处理，本轮不动。
- 实现阶段确认（已结论）：PySide6 6.12.0 与 PySide6-Fluent-Widgets 1.11.3 在 Python 3.12 下安装并共存成功，未走兜底方案。
- 实现分叉（已记录）：HTML 解析器基于标准库 html.parser，标签名统一按小写匹配，`Div` 与 `div` 等价；组件消息的 value 字段只在状态应答中携带；宿主的控制帧（status、command、shutdown）与消息帧分流处理，不进入消息总线。
