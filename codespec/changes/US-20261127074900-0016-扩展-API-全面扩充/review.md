---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 9 个命名空间 API（window/workspace/commands/env/extensions/storage/network/message/log）、ctx 不可变、窗口服务、状态栏/输出面板、网络服务与代理、设置页网络分类、文档技能 |
| 对应需求 | 命名空间与命名、window 五组、workspace、commands、env、extensions、storage、network 请求/多协议、网络代理设置、message、log、注册点、设置扩展 |
| 验证证据 | pytest 387 passed / 1 skipped；ruff F,E9 全过；网络单测 22 项含本地 HTTP/TCP/UDP 回环；窗口 API 37 项；workspace 11 项 |

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 一般 | api/commands.py | registerCommand 只发消息，宿主无法拿到 callback；处理：改为先 ctx.register_command 再发确认 | 代码审阅 | 接受 |
| R2 | 一般 | ui/window_api.py | 状态栏/输出面板直接加到主窗口 layout，未与既有布局统一 | 代码审阅 | 部分接受 |
| R3 | 一般 | app.py | onDidChangeActiveColorTheme 只返回订阅，主题切换未广播 | 代码审阅 | 接受 |
| R4 | 建议 | host.py | commands.register 仅确认，不重复注册（注册已在 ctx 完成） | 设计取舍 | 接受 |
| R5 | 建议 | network | SSH/SFTP/代理/QUIC 缺真机验证 | 环境限制 | 接受 |
| R6 | 建议 | window | withProgress 只显示进度对话框，取消与 task 进度回传未接线 | 代码审阅 | 接受 |

## 回归

- `uv run pytest -q` → 387 passed, 1 skipped
- `uv run ruff check obox tests --select F,E9` → All checks passed
- 网络：本地 HTTP/TCP/UDP 回环通过；代理策略单测覆盖

## 结论

- 严重：剩余 0 条
- 一般：R1 接受并已修；R2 需上游修正；R3 接受
- 建议：R4-R6 接受，R2/R3/R5/R6 列入 validation 遗留