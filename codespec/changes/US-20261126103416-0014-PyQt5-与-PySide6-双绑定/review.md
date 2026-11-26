---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 新增 obox/qt.py；137 处 import 收敛；事件坐标/图标/颜色/地区名兼容；--qt 与 pyqt5 extra；构建 --qt 与 CI 矩阵；文档 |
| 对应需求 | 双绑定兼容层、双绑定行为一致（ADDED）；依赖与安装包（ADDED） |
| 验证证据 | PySide6 310 passed；PyQt5 310 passed；verify 两绑定 × light/dark 各 0 失败；check_all 通过 |

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 一般 | 组件绘制 | PyQt5 的 QPen/QBrush 不接受 str 颜色，按钮 danger 文字崩溃（处理：统一 color() 转 QColor） | PyQt5 paint 异常 | 接受 |
| R2 | 一般 | 事件与图标 | Qt6 专有 position/globalPosition 与 QIcon.pixmap(size, dpr) 在 Qt5 不存在（处理：event_pos、icon_pixmap helper） | PyQt5 测试失败 | 接受 |
| R3 | 一般 | 语言列表 | Qt5 QLocale 无 nativeTerritoryName（处理：getattr 回退到 nativeLanguageName） | QLocale AttributeError | 接受 |
| R4 | 建议 | 图表 | PyQt5 下 teardown 时 draw_idle 定时器访问已删除画布（处理：改同步 draw） | 访问冲突 | 接受 |
| R5 | 建议 | 构建 | Nuitka 可能同时打包两套 Qt（处理：--nofollow-import-to 排除另一绑定） | 设计风险 | 接受 |
| R6 | 建议 | 测试 | pytest-qt 默认绑定可能与 OBOX_QT 不一致（处理：-o qt_api 对齐，CI 矩阵设置） | 混用崩溃 | 接受 |

## 回归

- PySide6：`uv run pytest -q` → 310 passed；verify light/dark → 0 失败
- PyQt5：`OBOX_QT=pyqt5 uv run pytest -q -o qt_api=pyqt5` → 310 passed；verify light/dark → 0 失败
- 门禁：`check_all.py` 全通过

## 结论

- 严重：剩余 0 条
- 一般：R1-R3 接受并已修
- 建议：R4-R6 接受并已修
