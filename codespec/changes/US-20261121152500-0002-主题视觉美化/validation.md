---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 本次结论 |
|---|---|---|
| `spec.md` / `design.md` | 是 | 无新增冲突；视觉统一一条与主题视觉规范的历史矛盾由 delta-spec 的 MODIFIED 收敛，基线本身留给收尾合并 |
| `proposal.md` | 是 | 1 处遗漏（需求草案缺视觉统一条目），已修 |
| `delta-spec.md` | 是 | 2 处问题（按钮区判定规则缺失、上限用词不一致），已修 |
| `delta-design.md` | 是 | 随 delta-spec 同步 1 处措辞，无独立问题 |
| `delta-arch.md` | 是 | 1 处措辞随上限统一，无独立问题 |
| `task.md` | 是 | 1 处建议（T7 断言偏弱），已补 |
| `scope.md` | 是 | 白名单与 T6-T14 逐条对齐，无越界项 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 严重 | `delta-spec.md` 浮层 | 没定哪些按钮进按钮区，实现必然二选一 | 原文「按钮区按声明顺序放 0 到 N 个按钮」未区分直接子级与正文内嵌按钮 | 已修复 |
| V2 | 一般 | `delta-spec.md` 浮层 | 上限用词不一致，会被理解成屏幕或窗口 | delta-spec 写「视窗的 90%」，delta-arch 写「宿主矩形 90%」 | 已修复 |
| V3 | 一般 | `proposal.md` 需求草案 | 缺视觉统一口径收敛这一条，与 delta-spec 的 MODIFIED 对不齐 | 需求草案原有 12 条，无视觉统一项 | 已修复 |
| V4 | 建议 | `task.md` T7 | 验收只跑 test_components.py，拖拽、reason、variant 无显式断言 | T7 原验收命令仅一条 pytest | 已修复 |

## 处理记录

- 第 1 轮：报告 4 项（严重 1 / 一般 2 / 建议 1），用户选择全部修复。
  - V1 修复：delta-spec.md:15 补「面板的直接子级 Button 进按钮区，其余子节点进正文区，正文内嵌套的 Button 保持原位」；delta-design.md 与 task.md:59 同步同一规则。
  - V2 修复：delta-spec.md:15 与 :30、delta-design.md:30、delta-arch.md:16 与 :64 统一为「宿主窗口的 90%」。
  - V3 修复：proposal.md:54 增第 13 条视觉统一口径。
  - V4 修复：task.md:59 补断言清单，覆盖按钮分区、三个 reason、close_on_overlay 默认关、尺寸 clamp、variant 三档、旧写法兼容。
  - 复核：`check.py --proj . --us US-20261121152500-0002-主题视觉美化` 返回 ok=true、0 issues。
- 第 2 轮：重跑结构与语义分析，无新增问题，收敛。
- 实现期（solver）：用户批准两次白名单扩展——`theme/*/components/button.py` 加 `set_variant`、`obox/api/events.py` 加 `CLOSE = "close"`（旧 modal 的 on_close 原本从未能投递）。另有一处未获答复的连带修复：`obox/ui/app_window.py:29` 引用已删除的 `_language_button`，两次提问均超时，为保证应用窗口可用已删该行，待用户追认。
- 实现期（solver）：关闭载荷的 value 取按钮文本（现成契约里 Button 没有 value 属性，button.py 不在本轮改造范围）。

## 遗留

- 已确认：CloseDialog 以主窗口为 parent 时能继承主题 QSS，遮罩实测 alpha 129，面板与按钮沿用 #obox-modal-card / QPushButton 规则。
- 已确认：拖拽缩放只改面板尺寸，宿主 Resize 过滤器只重设覆盖层几何，二者不互触发（test_modal_drag_resize_clamps_to_minimum 通过）。
- 已确认：verify_ui 新增 {theme}_17_modal 与 {theme}_18_modal_legacy，{theme}_11_lang_en 保留，语言场景改走 `_on_settings_set`。
- 待用户追认：obox/ui/app_window.py 删掉一行对已移除语言按钮的引用（两次扩白名单提问均超时未答）。
- 观察：浮层徽标用内联样式、CloseDialog 徽标走 #obox-modal-badge，两条路径并存；后续若要统一可把浮层徽标也改成对象名。