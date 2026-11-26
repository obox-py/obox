---
status: done
---

# Tasks

## 任务清单

| ID | 任务 | 方式 | 涉及文件 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 绑定层与导出 | 主 Agent | obox/qt.py | 双绑定兼容层 | - | OBOX_QT 选择、名称齐全、非法值报错 | 完成 |
| T2 | 全量 import 替换 | 主 Agent | obox/**、scripts/**、tests/** | 双绑定兼容层 | T1 | 无残留 PySide6/PyQt5 直接 import | 完成 |
| T3 | 差异适配 | 主 Agent | obox/qt.py、组件与窗口文件 | 双绑定行为一致 | T2 | 事件坐标/图标/字体/颜色在 PyQt5 下正常 | 完成 |
| T4 | CLI 与依赖 | 主 Agent | obox/main.py、pyproject.toml | 双绑定兼容层、依赖与安装包 | T3 | --qt 生效、pyqt5 extra 可装 | 完成 |
| T5 | 双绑定测试 | 主 Agent | tests/** | 双绑定行为一致 | T4 | PySide6 与 PyQt5 各 310 passed | 完成 |
| T6 | 双绑定验证 | 主 Agent | scripts/verify_ui.py | 双绑定行为一致 | T5 | 两绑定 × light/dark 各 0 失败 | 完成 |
| T7 | 构建与文档 | 主 Agent | scripts/build_*.py、CI、README、技能 | 依赖与安装包 | T6 | --qt 出包、矩阵就绪、文档说明 | 完成 |

## 任务详情

### T1 绑定层
- 步骤：绑定选择、统一命名空间、exec_app、event_pos、icon_pixmap
- 验收：`uv run python -c "import obox.qt; print(obox.qt.BINDING)"`

### T2 import 替换
- 步骤：按模块替换 137 处并清理残留
- 验收：`grep -rn 'from PySide6' obox scripts tests` 无输出

### T3 差异适配
- 步骤：字符串颜色转 QColor、Qt5 事件坐标、QIcon DPR、QLocale 地区名回退、图表同步绘制
- 验收：PyQt5 下 pytest 全绿

### T4 CLI 与依赖
- 步骤：--qt 在 import app 前写环境变量；pyproject 加 extra
- 验收：`OBOX_QT=pyqt5 uv run python -m obox --version`

### T5/T6 双绑定测试与验证
- 验收：两绑定 pytest 310 passed；verify 4 组 0 失败

### T7 构建与文档
- 验收：`scripts/build_installer.py --qt pyqt5` 产物名含 pyqt5；CI 有 binding 矩阵

## 测试策略

TDD：先以 PyQt5 运行既有测试暴露差异，再补兼容 helper；每个差异至少有一条回归用例或 verify 场景覆盖。

## 执行顺序

T1 → T2 → T3 → T4 → T5 ∥ T6 → T7

## 覆盖检查

- 双绑定兼容层：T1-T4
- 双绑定行为一致：T3、T5、T6
- 依赖与安装包：T4、T7

## 自检

- [x] 每条需求都有任务覆盖
- [x] 验收命令可执行
- [x] 依赖无环
- [x] 方式只用 主 Agent / subagent / 后台
