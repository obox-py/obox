---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 结论 |
|---|---|---|
| spec.md / design.md | 是 | 9 命名空间属新增能力，已用 ADDED 收敛 |
| proposal.md | 是 | 18 条需求与 delta 对齐 |
| delta-spec.md | 是 | 15 ADDED + 2 MODIFIED |
| delta-design.md | 是 | 9 模块 + 处理器 + 设置页 |
| delta-arch.md | 是 | 时序图与 UML 齐全 |
| task.md | 是 | 12 个任务覆盖全部需求 |
| scope.md | 是 | 白名单与任务一致 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 一般 | delta-spec | 「设置页」不是基线 Requirement 名 | check.py E_DELTA_REF | 已修复 |
| V2 | 一般 | task | 命名空间需求含大写 API，覆盖检查大小写不匹配 | check.py E_TASK_COVER | 已修复 |
| V3 | 建议 | design | 用尖括号占位符触发模板检查 | check.py 占位符 | 已修复 |
| V4 | 一般 | network | ICMP 无法走代理，需在文档明确 | 协议限制 | 已修复 |
| V5 | 建议 | ctx | 可变 dataclass 与「不可变」要求冲突 | 用户反馈 | 已修复 |
| V6 | 建议 | QUIC | aioquic 新增依赖未纳入打包验证 | 设计 | 待验证 |

## 遗留

- aioquic 在 Nuitka 安装包中的体积与可用性需构建后验证
- UDP/QUIC 的 SOCKS5 UDP associate 依赖代理服务端，需真机验证
- ICMP 依赖系统 ping，需在 Windows/Linux 分别验证
- 状态栏/输出面板已改由 main_window.attach_* 接到底部布局
- onDidChangeActiveColorTheme 已在切主题时广播
- withProgress 取消与 task 进度回传仍未接线
- SSH/SFTP 已用真机 113.44.210.175 验证（12 项）；SOCKS5/HTTP CONNECT 与 QUIC 未做真机验证