---
status: done
---

# Tasks

## 任务清单

| ID | 任务 | 方式 | 涉及文件 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 选择器消息与校验 | 主 Agent | obox/api/picker.py、tests/test_picker.py | 文件与目录选择器 | - | 参数校验与序列化测试通过 | 完成 |
| T2 | 本地浏览模型 | 主 Agent | obox/ui/picker.py、tests | 文件与目录选择器 | T1 | 过滤、排序、路径解析测试通过 | 完成 |
| T3 | 对话框界面 | 主 Agent | obox/ui/picker.py | 文件与目录选择器 | T2 | 快速访问/面包屑/搜索/列表可交互 | 完成 |
| T4 | 按窗口模态与路由 | 主 Agent | obox/app.py、tests | 文件与目录选择器 | T1 | 主窗口阻塞主窗口、App 窗口只阻塞自身 | 完成 |
| T5 | SSH 客户端 | 主 Agent | obox/ui/picker_remote.py、pyproject.toml | 远端文件浏览、依赖与安装包 | T1 | 连接/列目录/指纹/超时测试（假 Transport） | 完成 |
| T6 | SSH 接入对话框 | 主 Agent | obox/ui/picker.py | 远端文件浏览 | T3,T5 | 连接下拉与远端浏览可用 | 完成 |
| T7 | 示例与验证 | 主 Agent | extensions/demo、scripts/verify_ui.py | 文件与目录选择器 | T3 | verify 截图并断言路径返回 | 完成 |
| T8 | 文档与门禁 | 主 Agent | obox-ext-dev/oml.md、README | 文件与目录选择器、远端文件浏览、依赖与安装包 | T7 | check_all 通过 | 完成 |

## 测试策略

TDD：消息校验与本地模型先写失败测试；对话框用离屏实例断言过滤、多选与模态；SSH 用假 Transport 测连接与错误路径，不打真实网络。

## 执行顺序

1. T1 ∥ T2
2. T3 ∥ T5
3. T4
4. T6
5. T7
6. T8

## 覆盖检查

- 文件与目录选择器：T1-T4、T7
- 远端文件浏览：T5、T6
- 依赖与安装包：T5、T8

## 任务详情

### T1 消息与校验
- 步骤：新增 PICKER_OPEN/PICKER_RESULT，校验 mode、扩展名与 ssh
- 验收：`uv run pytest -q tests/test_picker.py`

### T2-T4 本地浏览、对话框与模态
- 步骤：Win11 风格对话框、本地枚举、按窗口 WindowModal
- 验收：verify 的 27_picker 场景与测试

### T5-T6 SSH
- 步骤：paramiko 客户端、后台线程、指纹确认、远端列目录
- 验收：真机 113.44.210.175 列出 / 与 /root

### T7-T8 验证与文档
- 步骤：verify 场景、扩展开发文档
- 验收：`uv run python .agents/skills/obox-test/scripts/check_all.py`

## 自检

- [x] 每条需求都有任务覆盖
- [x] 验收命令可执行
- [x] 依赖无环
- [x] 方式只用 主 Agent / subagent / 后台
