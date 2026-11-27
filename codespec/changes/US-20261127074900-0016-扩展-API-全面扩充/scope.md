---
status: done
---

# Scope

## 可改（白名单）

- `obox/api/*.py`（新增命名空间模块）
- `obox/extensions/context.py`、`host.py`
- `obox/extensions/network/**`（新）
- `obox/app.py`、`obox/ui/statusbar.py`、`obox/ui/output_panel.py`（新）
- `obox/ui/app_window.py`、`obox/ui/modal.py`、`obox/ui/picker.py`（小改）
- `extensions/settings/**`
- `pyproject.toml`、`uv.lock`
- `tests/**`
- `docs/api.md`、`docs/arch.md`、`README.md`
- `.agents/skills/obox-ext-dev/**`

## 明确不动

- `theme/**`、`extensions/{app,management,deprecated}`
- 扩展清单格式与 .oix 打包格式
- 既有 picker/app/settings 的消息语义（只增不改）
- CI workflow

## 越界处置

停手，报路径、理由与对应需求，确认后再改。
