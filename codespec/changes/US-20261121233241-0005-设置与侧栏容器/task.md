---
status: done
---

# Tasks

| ID | 任务 | 方式 | 涉及文件 | 需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 容器改为 sidebar | 主 Agent | obox/ui/main_window.py、obox/app.py、obox/extensions/manifest.py、extensions/{app,demo,gallery}/extension.json | 主界面三段布局 | - | 全仓无 main 容器；旧清单报错 | 完成 |
| T2 | 设置消息与配置贡献 | 主 Agent | obox/api/settings.py、obox/extensions/manifest.py | 扩展配置贡献、设置读写 | T1 | 配置项被校验汇总；消息可往返 | 完成 |
| T3 | 设置列表汇总与写入 | 主 Agent | obox/app.py | 设置读写 | T2 | theme/language 即时生效；写 config 成功 | 完成 |
| T4 | 设置扩展（系统扩展 settings/obox/1.0.0） | 主 Agent | extensions/settings/** | 设置扩展、设置搜索 | T3 | 清单为 name=settings、publisher=obox、version=1.0.0；侧栏入口、两栏布局、搜索过滤 | 完成 |
| T5 | 测试与验证 | 主 Agent | tests/、scripts/verify_ui.py | 全部 | T4 | 单测 + verify 断言设置页 | 完成 |
| T6 | 文档与合并 | 主 Agent | README.md、docs/arch.md、codespec/specs/ | 全部 | T5 | 基线合并，check 0 | 完成 |

## 任务详情

- T1：`uv run pytest -q tests/test_manifest_views.py`，容器白名单生效
- T2：`uv run pytest -q tests/test_manifest_configuration.py`，配置项校验
- T3：`uv run pytest -q tests/test_settings_store.py`，写入与回读
- T4：`uv run python scripts/verify_ui.py`，设置页渲染与搜索
- T5：`uv run pytest -q`，全量
- T6：`check.py --baseline-only`，0 问题

## 测试策略

容器与配置项走单测；设置页与即时生效走 verify_ui。

## 自检

- [x] 每条需求都有任务覆盖
- [x] 依赖无环
- [x] 验收命令可复制

## 执行顺序

1. T1 → T2 → T3 → T4 → T5 → T6