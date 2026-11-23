---
status: done
---

# 视图锚点 Design Delta

受影响的组件、依赖方向与流程时序由 df-arch 画在 delta-arch.md。本文件只写这次改哪里、为什么这么改、基线会怎么变。

## Context

视图在 obox 里被 QScrollArea 包住（obox/app.py 的 _mount_view 创建 obox-view-scroll），滚动位置没有对外接口，也没有吸顶、锚点与滚动高亮的概念。设置页改版后经复核要求还原，因此本次只保留通用能力。

## Scope

- 视图锚点与滚动（ADDED）
- 视图文件格式（MODIFIED）

## Changes

| 模块 | 改什么 | 对应需求 |
|---|---|---|
| `obox/api/view.py` | 新增滚动到锚点（view_id、anchor、offset、duration）与当前锚点变化（view_id、anchor）两条消息 | 视图锚点与滚动 |
| `obox/ui/anchor.py`（新） | 滚动控制器：锚点目标值、QPropertyAnimation 平滑滚动、按视口算当前锚点并回调 | 视图锚点与滚动 |
| `obox/app.py` | _mount_view 识别视图根直接子节点的 sticky 并把组件抬到滚动区上方；挂载控制器、订阅滚动消息、回推锚点事件 | 视图锚点与滚动、视图文件格式 |
| `tests/test_anchor.py`（新） | 消息往返、目标值与夹取、锚点归属、sticky 抬出与路由 | 视图锚点与滚动 |
| `.agents/skills/obox-ext-dev` | 文档补 sticky 属性与两条消息 | 视图锚点与滚动 |

## Decisions

- 锚点就是组件 id，且只认视图根的直接子组件；不做嵌套锚点。
- 吸顶在装配时把组件从滚动内容里取出，放到滚动区上方；只支持一个。
- 平滑滚动用 QPropertyAnimation 动滚动条 value，OutCubic，600ms 缺省；新请求替换旧动画。
- 当前锚点按「视口顶部 + 偏移」取最后一个越过的章节；到顶取第一章、到底取最后章节；只在变化时发事件。
- 设置页维持左分类右条目，不引入 sticky；本次能力暂由扩展按需使用。

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 按 delta-spec.md 的 1 条 ADDED 与 1 条 MODIFIED 合并；视图文件格式补 sticky 与锚点 |
| design.md | 新增 D36「视图锚点与滚动高亮」 |
| docs/arch.md | 4.1 分层图的外壳行补滚动控制器（图由 df-arch 落） |
| README.md | 能力清单补锚点能力 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| 内容高度变化导致动画目标过期 | scroll_to 每次按当前几何重算 |
| sticky 取出后原布局留白 | 取出时从原布局移除，不占位 |
| 滚动事件频繁 | 只在锚点变化时回推 |
| 多个 sticky 冲突 | 只取第一个，其余忽略 |

回滚：删 anchor.py 与两条消息，_mount_view 不再处理 sticky；设置页本就没有改动。
