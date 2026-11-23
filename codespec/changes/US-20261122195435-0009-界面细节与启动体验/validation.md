---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 本次结论 |
|---|---|---|
| `spec.md` / `design.md` | 是 | 无新增冲突；托盘与切换相关条目按 delta-spec 的 MODIFIED 收敛 |
| `proposal.md` | 是 | 9 条需求与 delta-spec 的 2 ADDED + 5 MODIFIED 对齐，无遗漏 |
| `delta-spec.md` | 是 | 2 处需补（应用窗口一致性、重建期菜单禁用），已修 |
| `delta-design.md` | 是 | 无独立问题 |
| `delta-arch.md` | 是 | 无独立问题 |
| `task.md` | 是 | 1 处验收偏弱（ico 校验），已修 |
| `scope.md` | 是 | 白名单与 T1-T10 逐条对齐，无越界项 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 一般 | `delta-spec.md` 运行中切换套件 | 切语言会关应用窗口、切主题不关，需求未写清 | app.py:171-173 语言分支 force_close，主题分支不关 | 已修复 |
| V2 | 一般 | `delta-spec.md` 托盘常驻 | 重建期间要禁用菜单项，只写在设计风险里 | delta-design 的 Risks 表有该条，spec 无场景 | 已修复 |
| V3 | 建议 | `delta-spec.md` 托盘常驻 | 「行高与留白接近参考」没有数值，之后无法核对 | 参考截图只在对话里 | 已修复 |
| V4 | 建议 | `task.md` T4 | 验收只跑 build_exe --help，没验证 ico 可加载 | T4 原验收命令 | 已修复 |

## 处理记录

- 第 1 轮：报告 4 项（严重 0 / 一般 2 / 建议 2），用户选择全部修复。
  - V1：delta-spec 的运行中切换套件补「切语言时独立应用窗口随之关闭，切主题时保留」。
  - V2：托盘常驻补 Scenario「重建期间菜单不可点」。
  - V3：托盘常驻写明面板宽 240、行高 44、圆角 10、左右内边距 14。
  - V4：T4 验收改为用 QIcon 加载 obox.ico 并断言含 256 尺寸，自检补"缺 ico 时构建日志写明退化"。
  - 复核：check.py 无 E_DELTA / E_TASK / W_PLACEHOLDER，只剩 validation.md 与 review.md 未生成。
- 第 2 轮：重跑结构与语义分析，无新增问题，收敛。

## 遗留

- 已确认：QMenu 开 WA_TranslucentBackground 后能吃到 #obox-tray-menu 的圆角与行高规则；真实桌面上的阴影由系统绘制，offline 截图无法覆盖，留人工核对。
- 已确认：AppUserModelID 在 run() 首行调用，早于 QApplication 创建。
- 已确认：obox.ico 由 obox.svg 生成，QIcon 可加载且含 256 尺寸；build_exe 在文件存在时追加 --windows-icon-from-ico，缺失时调 _render_icon 重新生成。
- 待用户决策（来自评审 R5）：supervisor.start() 未复位 _stopping，刷新后宿主崩溃不再自动拉起；修法一行，但 supervisor.py 在「明确不动」里，扩白名单的提问两次超时未答。
- 转入遗留（评审 R13）：_mount_view 的 rebuild 参数未被读取，属既有参数，删改需跨模块重构。
- 转入遗留（评审 R14）：_on_extensions_ready 里 _push_settings 调了两次，属既有顺序，删除可能改变配置下发时机。
- 转入遗留（评审 R22）：AppUserModelID 的调用序没有自动化断言，目前靠代码位置保证。
- 实现记录：新增测试 10 条（settings_label 2、app_switches 4、tray 3、icon 1），全量 241 passed。
- 实现记录：theme 常量的旧文档数值（圆角 10/16、控件 38）与代码不符，已随本次同步改为 2/2/32。