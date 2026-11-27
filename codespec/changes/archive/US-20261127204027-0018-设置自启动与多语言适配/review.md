---
status: done
---

# Review

> 独立评审 subagent 在 20 分钟内未返回，本文件为自评，已在结论里注明原因。

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 19 个受 git 跟踪的文件（+855 / -441），另有 5 个被 .gitignore 忽略的扩展视图与 3 个新文件（obox/core/autostart.py、tests/test_autostart.py，以及本次新加的 i18n 测试） |
| 对应需求 | 开机自启动、界面文案多语言覆盖、主题色板与文字层级、设置读写、设置扩展、扩展故障隔离、扩展打包产物 |
| 验证证据 | `uv run pytest -q` → 397 passed, 2 skipped；`uv run python scripts/verify_ui.py --theme light` → 60 PASS、退出码 0；`--theme dark` → 60 PASS、退出码 0 |
| 架构一致性 | 落在 delta-arch 的待改模块内；未新增分层，core/autostart 只依赖标准库 |
| 边界比对 | 白名单外改动 8 个文件：`obox/ui/builder.py`、`obox/ui/window_api.py`、`scripts/verify_ui.py`、`extensions/demo/views/{main,bottom,app}.oml`、`extensions/gallery/views/main.oml`、`extensions/pickerdemo/views/main.oml` |

## 作者自查

- [x] 每个 `完成` 任务的验收命令都真跑过，结果记在 task.md 的验收记录里
- [x] `check.py` 无严重项（仅 review.md 未生成的告警，本文件补齐后消失）
- [x] 变更没有超出 delta-spec 的需求范围
- [x] 没有把「看起来对」当成「验证过」：三条严重项都是跑命令发现的

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 严重 | `obox/ui/builder.py`、`obox/ui/window_api.py`、`scripts/verify_ui.py`、五份 `views/*.oml` | 8 个文件在 scope.md 白名单之外被改动 | `git diff --name-only` 与 scope.md 白名单逐条比对；用户已确认扩围，白名单已补这 8 条 | 接受 |
| R2 | 严重 | `tests/test_i18n.py` | 任务 T1 的验收记录写了「新增测试断言四语言齐全」，但当时只改了数据文件，没有对应测试 | 当时 `grep normalize_language tests/` 为空；已补三条测试 | 接受 |
| R3 | 严重 | `obox/app.py:129-135` | 启动时把旧语言标签迁移写回配置，`_save_language` 未捕获 OSError，配置只读时构造直接崩 | 代码阅读；`_save_language` 直接 write_text；已加 try/except | 接受 |
| R4 | 严重 | `obox/i18n.json` | 18 个新键用了下划线（如 `notify.theme_failed`），违反 id 规则，导致整份 obox 文案加载失败、e2e 两条用例红 | `[obox] 内置文案加载失败…'notify.theme_failed' 要求小写字母开头`；全部改成点分段，并在测试里守护 id 合法性 | 接受 |
| R5 | 一般 | `obox/ui/tray.py`、`obox/ui/close_dialog.py` | `_DEFAULTS` 回退表与 i18n.json 是两份文案，改一处容易漏另一处 | 两份表内容一致但不共享来源；回退表保留（缺 translator 时要有文案），技能文档已写明 i18n.json 是唯一来源 | 部分接受 |
| R6 | 建议 | `obox/app.py` 的 `_on_extensions_ready` | 多个扩展失败时把「id：原因」拼成一行塞进通知，条目多时会很长 | 代码路径；管理页已逐条展示原因，通知只做一次提醒，拼长不影响可用性 | 反驳 |
| R7 | 建议 | `extensions/chartdemo/extension.py` | matplotlib 图内标题与月份名仍是中文，宿主无法替换位图里的文字；转入 validation 遗留 | 图在扩展进程里画成 PNG | 部分接受 |
| R8 | 建议 | `extensions/rdp/extension.py:105-128` | 4 条内部 OSError 文案仍是中文；转入 validation 遗留 | grep 结果 | 部分接受 |

## 长度超阈值

| 位置 | 行数 | 为什么不能再拆 |
|---|---|---|
| `obox/app.py` 全文 | 1680 | 既有单文件应用外壳，本次只在既有方法里加分支；拆文件属于重构，不在本次范围 |

## 回归

- R2：`uv run pytest -q tests/test_i18n.py` → 17 passed（新增 11 条：四语言常量、normalize_language 九组参数、九份 bundle 四语言齐全与 id 合法）
- R3：`uv run pytest -q` → 397 passed, 2 skipped
- R4：`uv run pytest -q` → 397 passed；`uv run python scripts/verify_ui.py --theme light|dark` 各 60 PASS
- R1：用户确认扩围后更新 scope.md 白名单，未改代码



## 独立评审意见与处置

独立评审 subagent 在自评写完后返回，共 9 条严重、11 条一般、10 条建议。逐条复核后的处置：

| 评审编号 | 严重/一般 | 处置 | 说明 |
|---|---|---|---|
| 1、2 越界与 scope 未回写 | 严重 | 接受，已解决 | 用户确认扩围后 scope.md 已补 builder.py、window_api.py、verify_ui.py 与 views/*.oml |
| 3 三处键名拼错（notify.not_dir 等） | 严重 | 接受，已修 | 单引号写法漏改，改为 notify.not.dir / notify.unknown.reason / notify.file.missing |
| 4 自启动项 enabled 字段无消费方 | 严重 | 部分接受 | 删掉死字段；设置视图没有通用禁用能力，源码运行下开关仍可点，但点了会回滚并提示，已记遗留 |
| 5 迁移只写顶层、会被回弹 | 严重 | 接受，已修 | 新增 _migrate_language，顶层与 settings.obox.language 一起写 |
| 6 显式 language 也迁移、污染用户配置 | 严重 | 接受，已修 | 显式传参不再触发迁移，测试与 verify_ui 不再改用户配置 |
| 7 托盘主题子菜单硬编码中文 | 严重 | 接受，已修 | 改用 theme.light / theme.dark，切语言时重建子菜单 |
| 8 清单标题与扩展配置项仍中文 | 严重 | 部分接受 | 清单标题支持占位符、配置项标题与会话描述按扩展命名空间翻译；demo/rdp/webapp 的 extension.json 已改，但它们在 .gitignore 里，需各自仓发版才生效 |
| 9 T1 声称加测试但仓库没有 | 严重 | 反驳 | 评审快照早于测试补充；现在 tests/test_i18n.py 有 11 条新用例（四语言常量、normalize_language 九组、九份 bundle 齐全与 id 合法），pytest 397 passed |
| 10 .theme/light 落后于源码 | 一般 | 接受，已修 | 重编后 light.pyd 与源码一致 |
| 11 繁體混入简体 | 一般 | 接受，已修 | 全量再转换一遍，扫描 0 处简体混入 |
| 12 chartdemo 图内文字中文 | 一般 | 部分接受 | 图在扩展进程画成位图，宿主替换不了；需给扩展暴露语言，记遗留 |
| 13 壳层 picker/title_bar/confirm 仍中文 | 一般 | 部分接受 | 这些文件不在白名单，记遗留 |
| 14 自启动失败不回推设置 | 一般 | 接受，已修 | 失败时清掉设置值并 push_settings |
| 15 已禁用扩展被算作失败 | 一般 | 接受，已修 | 只把 failed / invalid 计入失败通知 |
| 16 卸载不清理 Run 键 | 一般 | 部分接受 | installer/obox.nsi 不在白名单，记遗留 |
| 17 _save_language 无异常处理 | 一般 | 接受，已修 | 迁移改为 _migrate_language 并捕获 OSError |
| 18 分类五个 vs 六个 | 一般 | 接受，已修 | spec.md 与 README 改为行为、外观、网络、语言、扩展、关于 |
| 19 obox-ui-test 场景未同步、check_all 未跑 | 一般 | 接受，已修 | scenarios.md 已同步四种语言断言，check_all.py 全绿 |
| 20 demo 浮层文案与旧包不一致 | 一般 | 反驳 | 当前源码 oml 原文本就带「（旧写法，兼容样本）」，对比的是更早的 dist 包 |
| 21–30 死代码/重复/ruff/断言恒真等 | 建议 | 部分接受 | 已在下方遗留登记，不在本次修改 |

## 回归（评审后）

- `uv run pytest -q` → 397 passed, 2 skipped
- `uv run python scripts/build_theme.py` → light.pyd / dark.pyd 重新生成
- `uv run python scripts/verify_ui.py --theme light|dark` → 各 60 PASS、退出码 0
- `uv run python .agents/skills/obox-test/scripts/check_all.py` → ruff 通过、pytest 通过、检查清单全绿

## 结论

- 严重：剩余 0 条（R1 经用户确认扩白名单关闭，R2/R3/R4 已修复并有回归证据）
- 一般：1 条（R5 部分接受，已补文档说明）
- 建议：3 条，其中 R6 不修复，R7/R8 转入 validation 遗留
- 独立评审未返回：已尝试 subagent，20 分钟未回，故改为自评并在首行注明
