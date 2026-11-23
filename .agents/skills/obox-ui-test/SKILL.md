---
name: obox-ui-test
description: 验证 obox 界面时使用。覆盖 ui_driver 能力、verify_ui 的场景与截图编号、常见坑；附一键跑 light/dark 验证并汇总结果的脚本。
---

# obox 界面验证

## 何时用

- 改了组件、主题、布局、设置页或应用页，需要看真实渲染
- 需要截图作为交付证据
- verify_ui 失败但不知道卡在哪个场景

## 快速开始

```bash
# 两套主题一起跑，汇总退出码与截图
uv run python .agents/skills/obox-ui-test/scripts/run_verify.py

# 单套、保留窗口
uv run python scripts/verify_ui.py --show --theme dark
```

## 步骤

1. 先确认 `.theme` 是最新构建（改过 theme/ 就要重编）
2. 跑 run_verify.py；失败时看返回的日志路径与截图
3. 需要新场景时，参照 `templates/scenario.py` 在 scripts/verify_ui.py 里加断言
4. 截图在 `tmp/pics/{theme}_NN_*.png`，编号固定（见 references/scenarios.md）
5. 交付前把关键截图贴进结论

## 参考

- `references/driver.md`：UiDriver 能力与等待策略
- `references/scenarios.md`：现有场景、断言与截图编号
- `references/pitfalls.md`：中文输入、配置污染、窗口截图等坑

## 边界

- 验证脚本用固定 `language=zh-CN`，避免被本地配置影响
- 截图只用于验收，不作为像素级回归基线
