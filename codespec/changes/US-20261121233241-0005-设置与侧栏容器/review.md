---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 容器 main→sidebar、设置系统扩展、配置贡献、设置读写与搜索 |
| 对应需求 | 主界面三段布局、注册点、设置扩展、扩展配置贡献、设置读写、设置搜索 |
| 验证证据 | 202 passed；verify light/dark 退出 0；截图 15_settings 与 16_settings_search；check 变更与基线 0 |
| 边界比对 | 全部落在白名单 |

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R7 | 严重 | extensions/settings/extension.py | 事件消息没有 component_id 属性，宿主抛异常并触发重启循环 | verify 在搜索输入时卡死，宿主日志 AttributeError | 接受 |
| R8 | 一般 | scripts/verify_ui.py | QTest.keyClicks 打不出中文，验证脚本挂起 | 探测脚本同一位置无输出 | 接受 |
| R9 | 一般 | extensions/settings/views/main.oml | 首版设置页用卡片堆分类，观感与 VSCode 不符；已新增 NavItem 组件并改为 VSCode 式两栏 | 截图对比 tmp/1.png：分类应是纯文本行 | 接受 |
| R10 | 一般 | .obox/config.json | 验证时的语言切换被持久化，后续测试读到 en-US 失败；测试与 verify 已显式传 language=zh-CN 并复位配置 | e2e 断言中文实际拿到英文 | 接受 |

## 回归

- `uv run pytest -q` → 202 passed（新增设置过滤、容器与配置校验用例）
- `verify_ui` light/dark → 退出码 0
- `check.py` 变更与基线 → 0 问题

## 结论

- 严重：剩余 0（R7 已修复）
- 一般：0（R8 已修复）