---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 新增 scripts/pack_extension.py；改造 extensions/loader.py、manifest.py、host.py、supervisor.py；新增 8 个测试；README 与 arch 补说明 |
| 对应需求 | 扩展打包产物、扩展安装、pyd 入口加载与模块搜索路径，加 MODIFIED 的扩展目录与清单 |
| 验证证据 | `uv run pytest -q` → 137 passed；实打包 gallery → dist/gallery.obox.0.1.0.oix；安装后隐藏源码目录，verify_ui 退出 0；ruff 全绿；check.py 0 问题 |
| 边界比对 | 改动全部落在 scope.md 白名单内（scripts、obox、tests、dist、.obox、docs/arch.md、README） |

## 作者自查

- [x] 打包、安装、加载三条路径都实际跑过
- [x] 源码扩展的加载没有被破坏（demo 仍从 extensions/ 加载）
- [x] 未改扩展 API 与消息协议

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 严重 | `scripts/pack_extension.py` | Nuitka 默认跟随 import，会把 obox 与依赖整个编进扩展 | 首版打包产物里出现 obox 模块；加 --nofollow-imports 后只编扩展自身 | 接受 |
| R2 | 严重 | `obox/extensions/host.py` | 多个打包扩展的入口 pyd 都叫 extension，模块名会互相覆盖；加载前覆盖并记录告警，文档要求扩展本地模块加前缀 | 加载时 sys.modules["extension"] 被后加载者替换 | 部分接受 |
| R3 | 一般 | `obox/extensions/loader.py` | zip 成员可带 ../ 写出安装目录 | 未校验成员路径 | 接受 |
| R4 | 一般 | `obox/extensions/loader.py` | 覆盖安装会残留旧文件 | 新包文件更少时旧文件仍在 | 接受 |
| R5 | 建议 | `scripts/pack_extension.py` | 逐文件编译耗时明显 | demo 单文件约 40 秒，多模块线性增长 | 接受 |

## 回归

- `uv run pytest -q` → 137 passed
- `uv run python scripts/pack_extension.py extensions/gallery` → dist/gallery.obox.0.1.0.oix
- 隐藏 extensions/gallery 后 `uv run python scripts/verify_ui.py` → 退出码 0（从 .obox/extensions 加载 pyd）
- `uv run ruff check obox tests scripts theme --select F,E9` → All checks passed

## 结论

- 严重：剩余 0 条（R1 已修复；R2 为已知约束，已用告警与文档降级）
- 一般：0 条（R3、R4 已修复）
- 建议：0 条待修（R5 记录实测）
