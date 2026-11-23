---
status: done
---

# Tasks

| ID | 任务 | 方式 | 涉及文件 | 需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 表达式求值器 | 主 Agent | obox/ui/expr.py | 模板指令与值绑定 | - | 路径/length/字面量/比较/! 单测通过 | 完成 |
| T2 | 模板指令与局部更新 | 主 Agent | obox/ui/template.py、obox/ui/builder.py | 模板指令与值绑定、视图数据与局部更新 | T1 | o-for/o-if/绑定可渲染；set_data 只重建受影响区域 | 完成 |
| T3 | 视图数据与生命周期 | 主 Agent | obox/app.py、obox/api/lifecycle.py | 视图数据与局部更新、视图生命周期 | T2 | 扩展收 data；mounted/updated/unmounted 送达 | 完成 |
| T4 | 应用清单与元数据 | 主 Agent | obox/extensions/manifest.py、obox/extensions/host.py | 应用注册、扩展目录与清单 | T3 | 多应用、icon/single/persistent 解析正确 | 完成 |
| T5 | App 系统扩展 | 主 Agent | extensions/app/** | 应用页作为系统扩展、应用网格 | T2、T4 | 侧栏出现应用页；网格由 o-for 渲染 | 完成 |
| T6 | 开窗与持久化 | 主 Agent | obox/api/app.py、obox/ui/app_window.py、obox/app.py | 打开应用与窗口复用 | T5 | single/persistent 四种组合行为正确 | 完成 |
| T7 | 测试与验证 | 主 Agent | tests/、scripts/verify_ui.py | 全部 | T6 | 单测 + verify 截网格与开窗 | 完成 |
| T8 | 文档与合并 | 主 Agent | README.md、docs/arch.md、codespec/specs/ | 全部 | T7 | 基线合并，check 0 | 完成 |
| T9 | 应用搜索 | 主 Agent | obox/api/app.py、obox/app.py、extensions/app | 应用搜索 | T8 | 输入过滤、清空恢复、越权忽略；子串单测 | 完成 |
| T10 | 扩展增删同步 | 主 Agent | obox/app.py、obox/extensions/supervisor.py | 应用搜索 | T9 | 目录变化后宿主重启并重新推送列表 | 完成 |
| T11 | 测试与验证 | 主 Agent | tests/、scripts/verify_ui.py | 应用搜索 | T10 | 单测 + verify 断言搜索过滤 | 完成 |
| T12 | 文档与合并 | 主 Agent | README.md、docs/arch.md、codespec/specs/ | 应用搜索 | T11 | 基线合并，check 0 | 完成 |

## 任务详情

- T1：`uv run pytest -q tests/test_expr.py`，覆盖路径、比较与真值
- T2：`uv run pytest -q tests/test_template.py`，覆盖 for/if 与局部更新
- T3：`uv run pytest -q tests/test_app_handlers.py`，覆盖视图数据与生命周期
- T4：`uv run pytest -q tests/test_manifest_apps.py`，覆盖多应用与图标
- T5：`uv run python scripts/verify_ui.py`，网格由 o-for 渲染
- T6：`uv run python scripts/verify_ui.py`，开窗与持久化
- T7：`uv run pytest -q`，全量
- T8：`check.py --baseline-only`，0 问题

## 测试策略

搜索与同步：过滤函数单测 + verify 输入关键字后卡片数变化；目录监听用临时目录单测。

单测覆盖表达式、模板、清单；端到端由 verify_ui 覆盖网格与开窗。

## 自检

- [x] 每条需求都有任务覆盖
- [x] 任务有验收命令
- [x] 依赖无环

## 执行顺序

1. T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8