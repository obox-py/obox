---
status: done
---

# 安装目录定位 Design Delta

## Context

Nuitka 冻结后各模块的 __file__ 与 __compiled__ 不可靠；sys.executable 指向 obox.exe，是最稳定的安装目录来源。

## Scope

- 程序目录解析（ADDED）

## Changes

| 模块 | 改什么 |
|---|---|
| obox/runtime.py | 新增 executable_path；is_installed 识别非 python 可执行文件；resolve 用其父目录 |
| tests/test_install_path.py | 伪造 obox.exe 验证 program_dir/system_extensions |

## Decisions

- 可执行文件名不是 python.exe/pythonw.exe/python3*.exe 时视为安装态
- OBOX_PROGRAM_DIR > exe 父目录 > 仓库根
- 保留 sys.frozen/__compiled__ 作为补充判断，不作为唯一依据

## Baseline Diff

| 基线 | 变化 |
|---|---|
| spec.md | 新增安装版程序目录定位 |
| design.md | 新增 D58 exe 路径定位 |
| docs/arch.md | 部署节补 program_dir 来源 |
| README.md | 安装版说明补系统扩展位置 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| 源码态 python.exe 被误判 | 显式排除 python/pythonw/python3 名称 |
| 绿色版无 exe 名 | OBOX_PROGRAM_DIR 覆盖 |
