---
status: done
---

# 执行边界

## 可改（白名单）

- `scripts/**`
- `obox/**`
- `tests/**`
- `dist/**`
- `.obox/**`
- `docs/arch.md`
- `README.md`
- `codespec/**`

## 明确不动

- `.git/**`：版本库内部。
- `.venv/**`：虚拟环境。
- `theme/**`：主题套件与本轮无关。
- `extensions/demo/`、`extensions/gallery/`：作为打包输入读取，不改。
- `tmp/task.md`：需求原文。

## 越界处置

执行阶段发现需要改白名单外的文件时停手，报告「需要改 X，因为 Y，对应 Z 需求」，确认后再补进白名单。
