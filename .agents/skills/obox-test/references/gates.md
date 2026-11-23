# 质量门禁

| 门禁 | 命令 | 通过判据 |
|---|---|---|
| 静态 | `uv run ruff check obox tests scripts theme extensions --select F,E9` | All checks passed |
| 测试 | `uv run pytest -q` | 无 failed / error |
| 文档 | `python <df-validation>/scripts/check.py --proj . --us <US>` | issues 0 |
| 基线 | 同上加 `--baseline-only` | issues 0 |
| 构建一致性 | `uv run python scripts/build_theme.py` 后无源码比 pyd 新 | find theme -newer 为空 |

Windows 注意：构建前关闭 obox，pyd 被占用会 PermissionError。
