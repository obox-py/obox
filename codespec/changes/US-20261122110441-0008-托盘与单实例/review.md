---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 单实例管道、托盘、关闭三选一、设置行为分类 |
| 对应需求 | 单实例运行、托盘常驻、关闭行为、关闭行为设置 |
| 验证证据 | 217 passed；verify light/dark 退出 0；新用例覆盖决策、管道、设置项 |
| 边界比对 | 只改 obox、tests、verify、文档 |

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 严重 | scripts/verify_ui.py | 收尾 close() 触发关闭询问对话框导致验证挂起；已改为收尾前 allow_close | verify 停在 04_final 后无输出 | 接受 |
| R2 | 一般 | obox/ui/single_instance.py | 客户端不等握手就断开，服务端收不到 show；已加 ack 与事件泵 | 单测收不到信号 | 接受 |
| R3 | 一般 | obox/app.py | 托盘对象退出时未清理；shutdown 已隐藏并 deleteLater | 潜在退出崩溃 | 接受 |

## 回归

- `uv run pytest -q` → 217 passed
- `verify_ui` light/dark → 退出 0
- `check.py` 变更与基线 → 本次合并后 0

## 结论

- 严重：剩余 0（R1 已修复）
- 一般：0（R2、R3 已修复）