---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | 第一轮：66 个 py 文件加配置与文档，删除根 main.py。第二轮：新增 theme/light 与 theme/dark 两套套件（各 17 个文件）、obox/ui/kit.py 与 component_protocol.py、scripts/build_theme.py，删除 obox/ui/components 与 obox/ui/theme.py，构建产物在 .theme（不入库） |
| 对应需求 | 基线 13 条 + delta ADDED 一条（主界面三段布局）+ 第二轮 8 条 ADDED（套件清单与加载、提供者契约、组件能力接口与消息分界、组件契约不变、视觉统一、运行中切换、构建与 pyd 产物、测试链路）+ 1 条 MODIFIED（组件事件上报改为声明式订阅） |
| 验证证据 | pytest 96 passed；scripts/verify_ui.py 退出码 0、8 项场景全 PASS（截图 tmp/pics、日志 tmp/logs）；ruff check 全绿；check.py 0 严重 |
| 架构一致性 | 实际模块与 delta-arch 的待改模块一致；依赖方向 ui 与 extensions 依赖 api 与 core，core 只依赖 api，无反向引用 |
| 边界比对 | 改动文件全部落在 scope.md 白名单内；本轮新增 .obox、.gitignore 两项边界登记，均在 scope.md 有据 |
| 评审方式 | 评审包交独立 subagent 评审，作者与评审者分离；作者对每条意见先复核再表态 |

## 作者自查

- [x] 每个完成任务的验收命令都真的跑过，并有输出
- [x] check.py 无严重项
- [x] 变更没有超出基线需求与 delta 的范围
- [x] 没有把「看起来对」当成「验证过」：每条修复都有新增用例或命令输出兜底

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 严重 | `obox/core/bus.py:123` | 应答里的 error 与 message 在重新编码时丢失，越权与不存在都变成成功应答 | reviewer 实测 reply 帧无 error；修复后 test_reply_payload 断言 E_FORBIDDEN_OWNER 能到达请求方 | 接受 |
| R2 | 严重 | `obox/app.py:55` | 宿主重启与扩展激活失败只打印到 stderr，界面没有任何提示 | 原 _on_host_state 只 print；docs/arch.md 却承诺顶部提示条 | 接受 |
| R3 | 严重 | `obox/api/message.py:45` | 扩展用 context.send 发消息后 obox 强制应答，缺 correlation_id 时抛异常 | 实测 ValueError 从总线处理器冒出；send 是公开能力 | 接受 |
| R4 | 一般 | `obox/app.py:66` | 宿主重启后重复装配同名视图，注册表冲突导致视图装配失败 | 重启后 stderr 报组件 id 冲突；e2e 只断言 ready | 接受 |
| R5 | 一般 | `obox/extensions/host.py:73` | 清单 contributes 只做键名校验，激活时不登记，声明与实现可脱节 | grep contributes 只命中 manifest；视图与命令全来自运行时注册 | 接受 |
| R6 | 一般 | `obox/app.py:131` | 越权分支永远走不到，跨扩展修改只会得到组件不存在 | lookup 已按 owner 过滤，owner 比较恒真 | 接受 |
| R7 | 一般 | `obox/app.py:115` | 样式路径按 owner 名反推，目录名与 name 不一致时静默失效；读文件未保护 | manifest 不校验目录名；read_text 在 try 之外 | 接受 |
| R8 | 一般 | `tests/test_bus.py:52` | 应答用例绕过 bus.reply 的真实编码路径，处理器没有行为用例 | test_bus 直接喂 dict；grep _on_modify 无命中 | 接受 |
| R9 | 一般 | `task.md:9` | delta-spec 已是 ADDED，task、delta-design、validation 仍按 Skipped 叙述 | 五处文档同时写过 Skipped | 接受 |
| R10 | 建议 | `obox/api/errors.py:52` | 死符号：StyleRejected、FrameDecoder.pending_bytes 无人使用 | grep 只命中定义与导出 | 接受 |
| R11 | 建议 | `obox/ui/components/select.py:14` | 列表切分函数在 select、tabs、table 三处逐字重复 | 三处函数体一致 | 接受 |
| R12 | 建议 | `README.md` | 运行产物 .obox 与安装产物 egg-info 未进忽略清单 | git status 会出现未跟踪目录 | 接受 |
| R13 | 严重 | `scripts/build_theme.py` | 构建产物与清单不同名时，加载器优先命中旧 pyd，界面实际跑的是上一版 | 重建后 .theme/dark 同时存在 dark.pyd（旧）与 dark.cp312 新产物，加载样式仍是旧版；已改为构建前清理并重命名 | 接受 |
| R14 | 严重 | `theme/_build/` | 只编译 __init__ 时，pyd 运行时找不到 theme 子包 | 首次构建后 import 报 ModuleNotFoundError: No module named 'theme'；改为 wrapper 加 --include-package=theme | 接受 |
| R15 | 一般 | `obox/app.py` | 按单个视图过滤扩展 QSS，同扩展其它视图的规则被误拒 | dark 启动日志出现 demo-title、demo-status、demo-btn 被拒；改为按扩展汇总 id 后统一下发 | 接受 |
| R16 | 一般 | `theme/dark/theme.py` | dark 只换按钮，窗口与内容区仍是浅色 | 截图显示浅底浅字；改为建窗口前切调色板、外壳样式交给 kit QSS、容器改 QFrame | 接受 |
| R17 | 建议 | `tests/test_kit_switch.py` | 全集运行时该用例偶尔在 teardown 报 RuntimeError | 连续三次全量运行出现一次；拆成 MainWindow 用例与 switch 用例后稳定 | 接受 |
| R18 | 建议 | `obox/ui/main_window.py` | FluentWindow 标题栏未随 dark 变色，顶栏与内容区色调不一致 | dark 截图的顶栏仍是浅色；留待下一轮主题打磨 | 部分接受 |

## 长度超阈值

| 位置 | 行数 | 为什么不能再拆 |
|---|---|---|
| `obox/extensions/manifest.py` 的 `load_manifest` | 59 | 已按意见拆成读取、身份、入口、图标、注册点、激活事件六个私有校验函数，每个函数只做一件事，主函数只负责串联。 |
| `scripts/verify_ui.py` 的 `main` | 63 | 保留：场景脚本按启动、点击、输入、命令、截图的顺序线性叙述，判断只有一个「侧栏按钮是否存在」的分支，拆成函数反而让读者来回跳。 |

## 回归

- `.venv/Scripts/python.exe -m pytest -q` → 96 passed（新增 test_app_handlers 5 例、test_reply_payload 2 例、e2e 重启后点击断言）
- `.venv/Scripts/python.exe scripts/verify_ui.py` → 退出码 0，8 项场景全 PASS
- `.venv/Scripts/python.exe -m ruff check obox tests scripts extensions --select F,E9` → All checks passed
- `python .../check.py --proj . --us US-...` → ok 为真，0 严重
- 第二轮 `uv run pytest -q` → 115 passed（连跑 3 次稳定）
- 第二轮 `uv run python scripts/verify_ui.py` → 退出码 0，截图 light_01 到 light_04
- 第二轮 `uv run python scripts/verify_ui.py --theme dark` → 退出码 0，截图 dark_01 到 dark_04
- 第二轮 `uv run python scripts/build_theme.py` → 两套 pyd 与 theme.json 齐全
- 第二轮 `uv run ruff check obox tests scripts theme --select F,E9` → All checks passed

## 结论

- 严重：剩余 0 条（第一轮 R1 到 R3、第二轮 R13 到 R14 全部修复并有回归证据）
- 一般：0 条（R4 到 R9、R15 到 R16 已修复，无遗留）
- 建议：0 条待修；R18（标题栏未随 dark 变色）记为下一轮主题打磨项
## 第五轮：移除第三方控件库

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R19 | 严重 | `theme/*/components/select.py`、`switch.py` | 换成 QComboBox 后原生箭头在 dark 下不可见，开关关闭态轨道几乎与背景同色 | 改造后首版截图里下拉框没有箭头、开关像白色药丸 | 接受 |
| R20 | 一般 | `obox/app.py` | 删除依赖后仍有 setTheme 调用残留，启动即 NameError | 首轮测试 7 例失败在 app.py:50 | 接受 |
| R21 | 一般 | `theme/*/components/notification.py` | InfoBar 属于被移除的库，通知组件必须换实现 | 依赖清点里 notification 仍导入 InfoBar | 接受 |

回归：

- `uv run pytest -q` → 151 passed（含 e2e）
- `uv run python scripts/verify_ui.py` / `--theme dark` → 退出码 0，截图 light_05 与 dark_05
- `grep -rn qfluentwidgets obox theme tests scripts extensions` → 0 处
- `uv sync` → 卸载 pyside6-fluent-widgets 及其依赖，pyproject 只剩 PySide6
- `check.py` 变更与基线均 0 问题

结论：严重剩余 0（R19 已修复并复看截图），一般项 R20、R21 已修复。
## 第六轮：控件过渡动画

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R22 | 建议 | `theme/*/components/button.py` | 按钮悬停是 QSS 瞬时切换，没有过渡 | 换掉控件库后悬停变化是硬切 | 接受：已把按钮改成自绘，hover 140ms、press 90ms |

回归：

- `uv run pytest -q` → 154 passed（test_animation 2 例、test_button_animation 1 例）
- `uv run python scripts/verify_ui.py` / `--theme dark` → 退出码 0
- `uv run ruff check obox tests scripts theme` → All checks passed
- `check.py` 变更与基线均 0 问题

结论：严重 0、一般 0、建议 0（R22 已修复并复测）。
## 第七轮：i18n 与 OML

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R23 | 一般 | `obox/app.py` | 扩展可以冒用别的 name 注册 i18n | 首版注册处理没有校验 name 与会话来源 | 接受：已限制 name 必须等于消息 src |
| R24 | 一般 | `obox/oml.py` | oml 路径可能越出扩展目录 | 相对路径可写 ../ | 接受：resolve 后校验父目录，越界直接失败 |

回归：

- `uv run pytest -q` → 164 passed（新增 test_i18n 6 例、test_oml 4 例）
- `verify_ui` light/dark → 退出码 0，新增断言「i18n 文案已替换」
- demo 与 gallery 的视图已迁到 `views/*.oml`，渲染结果与迁移前一致

结论：严重 0、一般 0。
## 第八轮：语言切换与 i18n.json

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R25 | 严重 | `obox/ui/registry.py`、`theme/*/components/alert.py` | 切语言时挂在窗口上的提醒条随组件注销被回收，动画仍在跑，重建视图时崩溃（退出码 139） | faulthandler 显示崩溃点在新卡片 connect，栈底是 switch_language | 接受：注销时调用 detach，停事件过滤器并 deleteLater |
| R26 | 一般 | `obox/i18n.py` | 扩展文案写在代码里，扩展作者要改文案得改 Python | 需求要求 i18n.json | 接受：新增 i18n.json 解析（数组与两种对象写法），host 读取后随视图一起下发 |

回归：

- `uv run pytest -q` → 172 passed（新增 i18n 文档与 detach 用例）
- `uv run python scripts/verify_ui.py` → 切到英文后视图重建断言通过，切回中文
- `check.py` 变更与基线 0 问题

结论：严重 0（R25 已修复），一般 0。
