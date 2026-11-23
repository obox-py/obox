---
status: done
---

# Validation

## 检查范围

| 文件 | 存在 | 本次结论 |
|---|---|---|
| `spec.md` / `design.md` | 是 | 无新增冲突；扩展安装与生命周期两节由 delta-spec 的 MODIFIED 收敛 |
| `proposal.md` | 是 | 10 条需求与 delta-spec 的 1 ADDED + 3 MODIFIED 对齐；禁用名单键名已回填 |
| `delta-spec.md` | 是 | 2 处需补（对话框归属、卸载确认步骤），已修 |
| `delta-design.md` | 是 | 无独立问题 |
| `delta-arch.md` | 是 | 无独立问题 |
| `task.md` | 是 | 2 处需补（打包脚本、确认框打桩），已修 |
| `scope.md` | 是 | 白名单与 T1-T10 对齐，obox/i18n.json 为对话框文案的必要落点 |

## 问题清单

| ID | 档位 | 位置 | 问题 | 证据 | 处理 |
|---|---|---|---|---|---|
| V1 | 一般 | `delta-spec.md` 扩展管理 | 安装按钮写成扩展自己打开文件框，但扩展进程没有对话框能力（写明动作消息由扩展发、文件选择由 obox 开） | 扩展跑在宿主进程，只有 obox 有 UI | 已修复 |
| V2 | 一般 | `delta-spec.md` / `task.md` T8 | 卸载确认框会阻塞自动化验证，场景未写处理方式（T8 写明卸载前把确认框打桩为直接确认） | verify_ui 是脚本驱动，模态框会卡住 | 已修复 |
| V3 | 建议 | `proposal.md` 假设 | 禁用名单键名写「实现时定」，与设计不一致（回填键名） | delta-design 已定为 extensions.disabled | 已修复 |
| V4 | 建议 | `task.md` T7 | 端到端测试没说用哪个脚本打包 .oix（写明用它打最小扩展） | 工程有 scripts/pack_extension.py | 已修复 |

## 处理记录

- 第 1 轮：报告 4 项（严重 0 / 一般 2 / 建议 2），用户授权自动确认后全部修复。
  - V1：delta-spec 扩展管理补「动作消息由扩展发、文件选择由 obox 开」；卸载场景补「在 obox 弹出的确认框里确认」。
  - V2：task T8 写明卸载前打桩确认框。
  - V3：proposal 的假设改为 extensions.disabled。
  - V4：task T7 写明用 scripts/pack_extension.py 打包最小扩展。
  - 复核：check.py 无 E_DELTA / E_TASK / W_PLACEHOLDER，只剩 review.md 未生成。
- 第 2 轮：重跑结构与语义分析，无新增问题，收敛。

## 遗留

- 已确认：宿主 _load_module 每次先写入 sys.modules 再 exec，同 id 重装会覆盖模块对象，旧代码不再运行；卸载只摘注册点，不承诺模块回收。
- 已确认：卸载当前视图时 app 先 show_view(DEFAULT_VIEW) 再 remove_view，视图集合与侧栏同步，测试 test_app_applies_removed_extension 覆盖。
- 已确认：禁用名单写在 config 的 extensions.disabled，宿主读 .obox/extensions/disabled.json 镜像；两者由一个写入点同步，测试 test_disabled_list_persists 覆盖。
- 实现记录：新增测试 6 条（消息、loader、宿主增删、过滤、差量应用、名单持久化），全量 249 passed。
- 实现记录：宿主身份改为 host.obox（消息 id 校验要求 name.publisher），控制消息走总线而非控制帧。
- 评审后遗留（R14）：changed 消息里的 changed 字段只用于状态刷新语义，commands 字段暂无消费方，保留作诊断。
- 评审后遗留（R23）：确认框与关闭框的文案仍硬编码中文，与既有 shell 对话框一致；如需多语言再补 i18n 键。
- 评审后遗留（R24）：verify_ui 只验扩展管理页与搜索过滤，安装/卸载的端到端由 tests/test_extension_manage.py 覆盖。