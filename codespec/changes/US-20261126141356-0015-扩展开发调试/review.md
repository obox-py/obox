---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | CLI --dev-extension/--debug；宿主 --dev-dir 与 dev 来源；DEV_ADD/REMOVE；debugpy；热重载；launch.json；文档 |
| 对应需求 | 开发扩展加载、断点调试、热重载、扩展目录与清单 |
| 验证证据 | pytest 4 条 dev 测试通过；PySide6/PyQt5 全量测试通过；check_all 通过 |

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 一般 | 宿主激活 | dev 结果缺 origin，列表显示 source | 探针 | 接受 |
| R2 | 一般 | 状态刷新 | 宿主重启后旧扩展不消失 | 移除探针 | 接受 |
| R3 | 建议 | debug | 首次激活要等 attach，否则看不到扩展 | debugpy 行为 | 接受 |
| R4 | 建议 | launch | 只有 attach 不够，补 launch 与 compound | 需求 | 接受 |
| R5 | 建议 | 热重载 | 断点期间保存会重启宿主，打断调试 | 设计取舍 | 接受 |

## 回归

- `uv run pytest -q tests/test_dev_extensions.py` → 4 passed
- 全量 pytest 与 check_all 通过

## 结论

- 严重：剩余 0 条
- 一般：R1、R2 接受并已修
- 建议：R3-R5 接受