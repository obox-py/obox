---
status: done
---

# Scope

## 可改（白名单）

- `obox/qt.py`（新）
- `obox/**/*.py`：仅替换绑定 import 与兼容差异
- `scripts/build_exe.py`、`scripts/build_installer.py`、`scripts/verify_ui.py`、`scripts/ui_driver.py`
- `tests/**`
- `pyproject.toml`、`uv.lock`
- `.github/workflows/build.yml`
- `README.md`、`docs/api.md`、`docs/UI.md`
- `.agents/skills/obox-ext-dev/**`

## 明确不动

- `codespec/**`
- `theme/**`
- `extensions/**`
- `installer/**`（安装脚本不变）
- `obox/api/**` 的消息与语义

## 越界处置

停手，报「需要改 某个路径，因为 某条理由，对应 某条需求」，确认后再改。
