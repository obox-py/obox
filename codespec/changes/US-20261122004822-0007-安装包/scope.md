---
status: done
---

# 执行边界

## 可改（白名单）

- `obox/**`
- `scripts/**`
- `installer/**`
- `tests/**`
- `docs/arch.md`
- `README.md`
- `.agents/skills/obox-ext-dev/**`
- `codespec/**`
- `build/**`、`dist/**`（构建产物）

## 明确不动

- `theme/**`、`extensions/**`：只读取，不修改
- `tmp/**`：需求与日志

## 越界处置

需要改安装器之外的东西才能出包时停手报告。
