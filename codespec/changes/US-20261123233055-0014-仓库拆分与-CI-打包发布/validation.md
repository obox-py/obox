---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 本次结论 |
|---|---|---|
| `spec.md` / `design.md` | 是 | 主题加载与构建两节由 MODIFIED 收敛 |
| `proposal.md` | 是 | 8 条需求与 delta-spec 对齐 |
| `delta-spec.md` | 是 | 2 处需补（oix 架构判定、系统扩展清单），已修 |
| `delta-design.md` | 是 | 无独立问题 |
| `delta-arch.md` | 是 | 无独立问题 |
| `task.md` | 是 | 8 个任务覆盖 5 条需求 |
| `scope.md` | 是 | 白名单与任务对齐 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 一般 | `delta-spec.md` 扩展目录 | 只写按架构选包，没说判定方式 | 需求原文 | 已修复 |
| V2 | 一般 | `delta-spec.md` 运行时资源 | 没写系统扩展清单与开发态回退 | 需求原文 | 已修复 |
| V3 | 建议 | `delta-spec.md` 构建 | ARM runner 不可用时的产物策略未写 | 平台未知 | 待验证 |
| V4 | 建议 | 仓库流程 | 三个仓库的初始内容边界未写 | 需求原文 | 待用户决策 |

## 遗留

- ARM64 托管 runner 是否对组织开放，建 workflow 后实测。
- 三个仓库的初始内容边界（主仓是否保留 extensions/rdp 与 webapp 副本）需在实现时定。
