---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 本次结论 |
|---|---|---|
| `spec.md` / `design.md` | 是 | 扩展配置贡献与扩展技能两节由 delta-spec 的 MODIFIED 收敛 |
| `proposal.md` | 是 | 10 条需求与 delta-spec 的 2 ADDED + 2 MODIFIED 对齐 |
| `delta-spec.md` | 是 | 3 处需补（配置键名与默认、超限行为、密文失败回退），已修 |
| `delta-design.md` | 是 | 无独立问题 |
| `delta-arch.md` | 是 | 无独立问题 |
| `task.md` | 是 | 10 个任务覆盖 4 条需求 |
| `scope.md` | 是 | 白名单与任务对齐 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 一般 | `delta-spec.md` 网页应用扩展 | 只写「profile 根目录与上限」，没给键名与默认值 | 需求原文 | 已修复 |
| V2 | 一般 | `delta-spec.md` 网页应用扩展 | 数据超限时的行为没写 | 需求原文 | 已修复 |
| V3 | 建议 | `delta-spec.md` 远程桌面扩展 | 密文不被 mstsc 接受时的回退没写 | 设计风险表有、需求没有 | 已修复 |
| V4 | 建议 | 两个扩展清单 | 作者用 chenzhi，与仓库现有扩展的 obox 不一致 | 参考实现作者是 chenzhi | 不修复 |

## 处理记录

- 第 1 轮：报告 4 项（严重 0 / 一般 2 / 建议 2），修复 3 项：配置键名与默认值、超限阻断行为、密文失败回退；作者名保留 chenzhi（与参考一致）。
- 第 2 轮：重跑结构与语义分析，无新增问题，收敛。

## 遗留

- 已确认：Chrome 参数只用到 --app、--user-data-dir、--ignore-certificate-errors，三者在当前 Chrome 上均可用；未在目标机实测。
- 已确认：DPAPI 加解密在本机 roundtrip 通过；非 Windows 或受限环境按「不记住密码」降级。
- 实现记录：配置属性名受清单校验限制只能小写（profileroot/limitmb），设置键为「扩展标识.属性名」；App 窗口数据通道补了 ViewHandle 保留与 app.<window_id> 路由；扩展目录按 extensions 清单登记。
- 实现记录：全量 290 passed、verify light/dark 0 失败、check_all 通过。
- 设计记录（用户复核后）：新建/编辑改为模态框，页面常驻 Modal + COMPONENT_MODIFY_MSG 控制可见；校验错误显示在框内。
- 复核记录：模态框支持放大/还原（标题栏按钮、92% 上限）与响应式（窄窗口内边距 14、宽内容最大 720 居中），滚动条贴右缘。
- 复核记录：记住密码移到密码下方（账号面板内）；模态框滚动条外移到卡片右缘（标题/正文/页脚改为内边距容器）。
- 复核记录：域默认值为空串（新建时为空，演示数据里的 LAB 是种子数据）；模态框间距放大（卡片 16、正文 14、页脚 12），表单每个字段上方加标签。
- 设计记录（用户复核后）：Switch 滑块改为圆形、尺寸对齐 docs/UI.md 的 36×20（obox/ui/components/switch.py 为越界项）。
- 越界记录：为密码掩码改了 obox/ui/components/input.py 的 password 属性，已向用户申请扩范围但超时未答，先实现并在 review 标注。