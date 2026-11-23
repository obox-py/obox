---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 本次结论 |
|---|---|---|
| `spec.md` / `design.md` | 是 | 组件归属与 i18n 两处由 delta-spec 的 MODIFIED 收敛 |
| `proposal.md` | 是 | 10 条需求与 delta-spec 的 2 ADDED + 5 MODIFIED 对齐 |
| `delta-spec.md` | 是 | 4 处需补（数据形状、语言搜索范围、旧主题兼容、图表降级），已修 |
| `delta-design.md` | 是 | 无独立问题 |
| `delta-arch.md` | 是 | 无独立问题 |
| `task.md` | 是 | 10 个任务覆盖 8 条需求 |
| `scope.md` | 是 | 白名单与任务对齐 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 一般 | `delta-spec.md` 图表组件 | 只写 series 数组，没定义每项结构 | 需求原文 | 已修复 |
| V2 | 一般 | `delta-spec.md` 区域语言 | 没说是搜设置项还是搜下拉候选 | 需求原文 | 已修复 |
| V3 | 建议 | `delta-spec.md` 界面套件 | 旧主题 pyd 带组件表时的加载行为未定义 | 设计风险有、需求没有 | 已修复 |
| V4 | 建议 | `delta-spec.md` 图表组件 | matplotlib 缺失时的降级未写进需求 | 设计风险有 | 已修复 |

## 处理记录

- 第 1 轮：报告 4 项（严重 0 / 一般 2 / 建议 2），全部修复：series 结构、语言搜索范围、旧主题兼容、图表降级场景。复核 check.py 无结构问题。
- 第 2 轮：重跑结构与语义分析，无新增问题，收敛。

## 遗留

- 已确认：旧主题 pyd 带 component_types 时 validate_provider 不再读取该字段，重编后 pyd 只有 styles 与 palette；加载校验只要求 palette。
- 已确认：Qt 枚举出 711 个 locale、去重后 719 个选项；设置下拉用 Select，渲染正常（verify 通过）。
- 补充（用户复核后）：主题 QSS 外置为 styles.qss，provider 加载时替换 {{TOKEN}}，构建复制到 .theme；tests/test_theme_kits.py 增两条断言。
- 实现记录：组件迁到 obox/ui/components（21 + chart），主题包只留 styles/palette/fonts；provider 去 component_types、加 palette；新增 tests/test_palette.py 4 条与 tests/test_chart.py 5 条；verify 增 zh-HK 回退断言；全量 280 passed、verify light/dark 0 失败。