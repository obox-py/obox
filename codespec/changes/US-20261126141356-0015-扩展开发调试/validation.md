---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 结论 |
|---|---|---|
| spec.md / design.md | 是 | 扫描来源与 CLI 需 ADDED/MODIFIED，已收敛 |
| proposal.md | 是 | 9 条需求与 delta 对齐 |
| delta-spec.md | 是 | 3 条（2 ADDED + 1 MODIFIED） |
| delta-design.md | 是 | 8 个模块行 |
| delta-arch.md | 是 | 待改 6 处 |
| task.md | 是 | 6 个任务 |
| scope.md | 是 | 白名单与任务一致 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 一般 | 宿主扫描 | dev 目录是扩展本身，scan_all 只扫父目录 | host.py 结构 | 已修复 |
| V2 | 一般 | 状态刷新 | 宿主重启后旧扩展残留，因状态只增不删 | 移除探针 | 已修复 |
| V3 | 建议 | origin | 激活结果缺 origin，dev 被显示成 source | 探针输出 | 已修复 |
| V4 | 建议 | debug | launch 与 attach 容易混淆 | VS Code 配置 | 已修复 |

## 遗留

- debugpy 等待 attach 时宿主不启动扩展，需在 VS Code 先启动 attach；文档已写
- 开发目录覆盖同 id 已安装扩展只在本次会话生效