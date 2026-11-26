# 测试矩阵

| 层 | 范围 | 命令 | 前置 |
|---|---|---|---|
| 单测（源码） | 解析、装配、模板、清单、i18n、oml、设置过滤 | `uv run pytest -q --ignore=tests/test_e2e.py` | 无 |
| e2e | 启动宿主、激活 demo/gallery/app/settings、消息往返 | `uv run pytest -q tests/test_e2e.py` | `.theme/light/light.pyd` |
| pyd 集成 | 主题套件加载与组件契约 | `uv run pytest -q tests/test_kit_loader.py tests/test_kit_switch.py` | 构建产物 |
| UI 验证 | 截图与交互 | 交给 obox-ui-test 的 run_verify.py | 构建产物 |

## 组件测试写法

用 `tests/fake_provider.py` 的假 provider + `Builder`，不需要 Qt 窗口；`qapp` fixture 由 pytest-qt 提供。