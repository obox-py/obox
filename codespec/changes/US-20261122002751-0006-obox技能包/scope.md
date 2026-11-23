---
status: done
---

# 执行边界

## 可改（白名单）

- `.agents/**`
- `README.md`
- `AGENTS.md`
- `docs/arch.md`
- `codespec/**`

## 明确不动

- `obox/**`、`theme/**`、`extensions/**`、`tests/**`、`scripts/**`：本轮只写技能，不改运行时。
- `tmp/**`：需求与日志。

## 越界处置

需要改运行时才能让脚本跑通时，停手报告「需要改 X，因为 Y」。
