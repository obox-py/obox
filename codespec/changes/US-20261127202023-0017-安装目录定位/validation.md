---
status: done
---

# Validation

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 一般 | runtime | is_installed 只认 sys.frozen/__compiled__，Nuitka 下不可靠 | 安装版症状 | 已修复 |
| V2 | 建议 | runtime | 需要保留 OBOX_PROGRAM_DIR 覆盖 | 绿色版/测试 | 已修复 |
| V3 | 建议 | 安装包 | 旧安装目录只有 app/settings，缺 management | 本机 Program Files 检查 | 待验证 |

## 遗留

- 需要用 1.0.1 安装包在本机静默安装后确认三个系统扩展加载