---
status: done
---

# Scope

## 可改（白名单）

- `obox/api/picker.py`
- `obox/app.py`
- `obox/ui/picker.py`、`obox/ui/picker_remote.py`
- `pyproject.toml`、`uv.lock`
- `tests/test_picker.py`
- `scripts/verify_ui.py`
- `extensions/demo/**`
- `.agents/skills/obox-ext-dev/**`
- `README.md`

## 明确不动

- `codespec/**`
- `obox/core/**`、`obox/api/**` 除 picker.py
- `obox/ui/components/**`、`obox/ui/main_window.py`、`obox/ui/app_window.py`
- 其它 `extensions/**`
- `theme/**`
- 安装包与 CI 脚本（paramiko 由依赖自动带入）

## 越界处置

停手，报「需要改 某个路径，因为 某条理由，对应 某条需求」，得到确认再改。
