---
status: done
---

# 执行边界

## 可改（白名单）

- `pyproject.toml`
- `main.py`（仓库根，按 T1 删除）
- `obox/**`
- `extensions/**`
- `tests/**`
- `docs/arch.md`
- `README.md`
- `tmp/obox.svg`
- `codespec/**`
- `scripts/**`
- `theme/**`
- `.theme/**`
- `tmp/pics/**`
- `tmp/logs/**`
- `.obox/**`（运行期扩展存储目录，由宿主进程写入）
- `.gitignore`（只补充运行产物与缓存的忽略项）
- `uv.lock`（uv 解析依赖生成的锁文件）

依赖白名单内路径即可覆盖 task.md 全部任务的涉及文件：T1 的 pyproject.toml 与 obox 骨架、T2 的安装命令产物、T3 到 T8 的 obox/api 与 obox/core、T9 到 T18 的 obox/ui 与 obox/extensions、T19 的 extensions/demo、T20 的 tests、T21 的 README 与 docs/arch.md。

## 明确不动

- `.git/**`：版本库内部，禁止直接改。
- `.venv/**`：虚拟环境，只由安装命令写入。
- `.python-version`：运行时版本锁定，本次不调。
- `.gitignore`：忽略规则本次不变。
- `.agents/**`：会话工具目录，与实现无关。
- `tmp/task.md`：需求原文，只读。
- 设置界面与套件选择入口：本轮不做，扫描结果只供启动选择与命令行使用。

白名单与不动清单无交集；`tmp/obox.svg` 只允许迁出后删除，不允许改写内容。

## 越界处置

执行阶段发现需要改白名单外的文件时，一律停手，向用户报「需要改 X，因为 Y，对应 Z 需求」，得到确认后才把该路径补进白名单再继续。不许先改后补，也不许用临时脚本绕过边界；已经被判越界的改动要回滚到改动前的状态。
