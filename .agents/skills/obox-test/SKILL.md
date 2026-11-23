---
name: obox-test
description: 跑 obox 的测试与质量门禁时使用。覆盖单测/e2e/pyd 集成矩阵、ruff、check.py 基线校验与排障；附一键汇总脚本与组件测试模板。
---

# obox 测试与检查

## 何时用

- 改完代码要跑一遍测试与静态检查
- e2e 需要 pyd 或宿主，失败看不出原因
- 交付前确认 codespec 基线仍然一致

## 快速开始

```bash
# 静态检查 + 全部测试 + 各 US 基线校验
uv run python .agents/skills/obox-test/scripts/check_all.py

# 只跑测试
uv run pytest -q

# 只跑单条
uv run pytest -q tests/test_manifest_apps.py
```

## 步骤

1. `uv sync`（首次或依赖变化）
2. 需要 e2e 时先 `uv run python scripts/build_theme.py`（e2e 用 pyd）
3. `uv run pytest -q`；失败先看是否配置污染（.obox/config.json 的 language/theme）
4. `uv run ruff check obox tests scripts theme extensions --select F,E9`
5. `check.py --us <US> --baseline-only` 确认文档结构
6. 交付前跑 check_all.py 汇总

## 参考

- `references/matrix.md`：测试矩阵与前置条件
- `references/gates.md`：质量门禁命令与判据
- `references/troubleshooting.md`：常见失败与处理

## 边界

- 不修改源码；失败只报告位置与证据
- 涉及 UI 的验收交给 obox-ui-test 技能
