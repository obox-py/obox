---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 组件从 theme/{light,dark}/components 迁到 obox/ui/components（21 + chart）；新增 obox/ui/palette.py、tests/test_palette.py、tests/test_chart.py；theme 两套改为 styles + palette；provider 契约、component_protocol、builder、kit、app 相应调整；i18n 回退链与全量地区语言项；pyproject 加 matplotlib |
| 对应需求 | 图表组件、区域语言与缺省回退（ADDED）；界面套件清单与加载、组件契约不变、组件能力接口与消息处理分界、主题色板与文字层级、i18n 注册与占位替换、设置扩展（MODIFIED） |
| 验证证据 | `pytest -q` → 280 passed；`verify_ui --theme light|dark` → 各 0 失败；`check_all.py` → 全通过；`check_theme.py` → 22 个宿主组件、调色板 20 项 |

## 作者自查

- [x] 每个 `完成` 任务的验收命令都真的跑过，并有输出
- [x] `check.py` 无严重项
- [x] 变更没有超出 delta-spec 的范围
- [x] 没有把"看起来对"当成"验证过"

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 一般 | `obox/ui/palette.py` | 活动调色板是进程级全局，同一进程不能同时渲染两套主题（项目本来就是单主题窗口；palette() 未初始化时回退亮色） | 设计决策 | 接受 |
| R2 | 一般 | `obox/ui/components/chart.py` | matplotlib 缺失时只显示提示，不提供安装引导（提示文案已给；安装属于环境问题） | ImportError 分支 | 接受 |
| R3 | 一般 | `obox/app.py` `language_options` | 全量 719 项在设置下拉里很长，且原生名有重名（补代码区分）（重名补地区代码；搜索框可过滤分类与候选项（后续如需下拉内搜索再补）） | 实测 711 locale / 719 选项 | 接受 |
| R4 | 建议 | `.agents/skills/obox-theme-dev` | 主题文档与脚手架仍按「主题含组件」写（本次改了 SKILL 与校验脚本；脚手架脚本留到主题开发专项） | SKILL 与 check_theme 已改，scaffold_component.py 仍指向主题目录 | 部分接受 |
| R6 | 一般 | `theme/*/theme.py` | QSS 藏在 pyd 字符串里，无法直接交付与审阅（处理：抽出 styles.qss，用 双花括号包裹的键名 引用调色板，provider 加载替换，构建复制到 .theme） | 用户复核意见 | 接受 |
| R5 | 建议 | `obox/ui/components` | 组件从主题复制后没有逐行对照，靠测试与截图回归（21 个组件的既有测试全绿，两套 verify 截图一致） | 迁移方式 | 接受 |

## 长度超阈值

| 位置 | 行数 | 为什么不能再拆 |
|---|---|---|
| `obox/ui/components/table.py` | 210 | 表格的列定义、单元格渲染与选中逻辑耦合在一处，拆开要重复列解析 |
| `obox/app.py` | 1380 | 装配中枢：视图挂载、锚点、扩展管理、设置与语言都在这里；拆分牵动 7 个调用点 |

## 回归

- 组件迁移：`uv run pytest -q` → 280 passed（含 21 个组件的既有用例）
- 图表：`uv run pytest -q tests/test_chart.py` → 5 passed
- 调色板：`uv run pytest -q tests/test_palette.py` → 4 passed
- 语言：`uv run pytest -q tests/test_i18n_switch.py` → 通过（zh-HK/zh-TW/en-GB/fr-FR 回退）；verify 增 zh-HK 回退断言
- 主题契约：`check_theme.py` → 两套各 22 个宿主组件、调色板 20 项；`check_all.py` → 全通过

## 结论

- 严重：剩余 0 条
- 一般：R1、R2、R3 接受并记录取舍
- 建议：R4 部分接受（脚手架脚本后续专项）；R5 接受（以测试与截图作为迁移证据）