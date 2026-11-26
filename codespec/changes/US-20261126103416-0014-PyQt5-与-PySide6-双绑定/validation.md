---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 结论 |
|---|---|---|
| spec.md / design.md | 是 | PySide6 单绑定需 MODIFIED，已在 delta 收敛 |
| proposal.md | 是 | 8 条需求与 delta 对齐 |
| delta-spec.md | 是 | 3 条（2 ADDED + 1 MODIFIED） |
| delta-design.md | 是 | 7 个模块行 |
| delta-arch.md | 是 | 待改 6 处，关联 3 处不动 |
| task.md | 是 | 7 个任务覆盖 3 条需求 |
| scope.md | 是 | 白名单与任务一致 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 一般 | 兼容层 | 只写统一导出，没写差异 helper 的范围 | 设计初稿 | 已修复 |
| V2 | 一般 | 构建 | 只说按绑定出包，没写排除另一绑定 | 设计初稿 | 已修复 |
| V3 | 建议 | 依赖 | PyQt5 的 extra 名称与 CI 安装方式未定 | 需求原文 | 已修复 |
| V4 | 建议 | 测试 | 两绑定同进程混用风险未写 | 实测崩溃 | 已修复 |

## 遗留

- PyQt5 下部分系统字体渲染与 PySide6 略有差异，verify 截图已对比。
- PyQt5 的 arm64 轮子需 CI 实测（当前仅 x64 构建）。