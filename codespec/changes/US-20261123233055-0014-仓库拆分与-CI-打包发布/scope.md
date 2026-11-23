---
status: done
---

# Scope

## 目标范围

主题与扩展的双源目录、按架构安装、构建与安装包结构、三个仓库的 CI 与远端发布。由仓库与发布流程、运行时资源目录、界面套件清单与加载、构建与 pyd 产物、扩展目录与清单五条需求驱动。

## 可改（白名单）

- `obox/runtime.py`、`obox/ui/kit.py`、`obox/app.py`、`obox/extensions/host.py`
- `scripts/build_theme.py`、`scripts/build_exe.py`、`scripts/build_installer.py`、`scripts/pack_extension.py`
- `installer/obox.nsi`
- `.github/**`
- `extensions/rdp/**`、`extensions/webapp/**`
- `tests/**`
- `README.md`、`docs/arch.md`
- `.agents/skills/obox-test/**`

## 明确不动

- `codespec/**`
- `obox/core/**`、`obox/api/**`、`obox/ui/components/**`、`obox/ui/main_window.py`
- `extensions/app/**`、`extensions/settings/**`、`extensions/management/**`、`extensions/gallery/**`、`extensions/demo/**`
- `theme/**`（本次只改产物布局，不改主题内容）
- `pyproject.toml`、`uv.lock`

## 越界处置

停手，报「需要改 某个路径，因为 某条理由，对应 某条需求」，拿到用户确认后再扩范围。
