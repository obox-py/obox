---
status: done
---

# Tasks

## 拆分方式

按可验证增量：消息契约、loader 单包能力、宿主控制处理、obox 编排、界面与确认框、管理扩展本体、测试、验证脚本、文档各自独立；共 10 个任务，前两项可并行起，其余按依赖串行。

## 全局约束

- 宿主仍是扩展生命周期唯一持有者；obox 不 import 宿主内部实现，只发消息
- 三个系统扩展之外不新增扩展；管理扩展只注册一个 sidebar 视图
- 卸载与停用只对用户安装来源开放，系统与源码来源在宿主与界面两层都要挡
- 不改扩展清单格式与打包格式；禁用名单只写 config
- 不引入第三方依赖

## 任务清单

| ID | 任务 | 方式 | 涉及文件 / 模块 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 扩展控制消息契约 | 主 Agent | obox/api/extensions.py、tests/test_extension_manage.py | 扩展安装、扩展管理 | - | 四条消息可构造、可往返，载荷字段有测试 | 完成 |
| T2 | loader 单包安装与卸载 | 主 Agent | obox/extensions/loader.py、tests/test_extension_manage.py | 扩展安装 | - | install_one/remove_one 可单包调用，扫描忽略 incoming | 完成 |
| T3 | 宿主控制消息处理 | 主 Agent | obox/extensions/host.py、tests/test_extension_manage.py | 扩展安装、扩展生命周期与上下文注入 | T1,T2 | 安装/卸载/启停各自摘挂注册点并回推 changed，单测覆盖 | 完成 |
| T4 | obox 编排与增量应用 | 主 Agent | obox/app.py、tests/test_extension_manage.py | 扩展安装、扩展目录与清单 | T3 | 收 changed 后按扩展 id 挂/摘视图，禁用名单写入 config，测试覆盖 | 完成 |
| T5 | 摘视图与卸载确认框 | 主 Agent | obox/ui/main_window.py、obox/ui/confirm_dialog.py | 扩展管理 | - | remove_view 可摘任意视图，确认框返回确认/取消 | 完成 |
| T6 | 扩展管理扩展本体 | 主 Agent | extensions/management/** | 扩展管理 | T4,T5 | 清单合法、页面渲染安装按钮/搜索/卡片，过滤函数有单测 | 完成 |
| T7 | 端到端测试 | 主 Agent | tests/test_extension_manage.py | 扩展安装、扩展管理 | T6 | 从 .oix 到卡片与视图出现、卸载后消失的整链路测试 | 完成 |
| T8 | 界面验证场景 | 主 Agent | scripts/verify_ui.py | 扩展管理 | T7 | 管理页截图、安装后侧栏多入口、卸载后消失，两套主题 0 失败 | 完成 |
| T9 | 扩展开发技能同步 | subagent | .agents/skills/obox-ext-dev/** | 扩展安装、扩展管理 | T3 | 文档写明控制消息、管理页写法、禁用名单，check_all 通过 | 完成 |
| T10 | 重编与全量验证 | 后台 | .theme、tests、scripts/verify_ui.py | 全部 | T8,T9 | pytest 全绿、verify 两套 0 失败 | 完成 |

## 任务详情

### T1 扩展控制消息契约

- 步骤：
  1. 新建 obox/api/extensions.py，定义 install/remove/enable 三条控制消息与 changed 回推、list 推送的 msg_id 与构造/解析
  2. 在 tests/test_extension_manage.py 写往返测试：构造消息后解码字段一致，非法载荷报错
- 验收命令：`uv run pytest -q tests/test_extension_manage.py -k message`（期望：全绿）
- 自检：字段命名与既有 api/*.py 一致；不用 Any 糊过去

### T2 loader 单包安装与卸载

- 步骤：
  1. loader 增加 install_one(package, install_root) 与 remove_one(install_root, extension_id)
  2. 启动扫描显式忽略 incoming 子目录
  3. 测试覆盖：安装出目录、卸载删目录、incoming 被忽略
- 验收命令：`uv run pytest -q tests/test_extension_manage.py -k loader`（期望：全绿）
- 自检：路径越界仍被拒绝；卸载不碰非用户目录

### T3 宿主控制消息处理

- 步骤：
  1. host 订阅三条控制消息；安装走 install_one + _activate；卸载调 deactivate 并 unregister_owner；启停切换激活状态
  2. 每个动作后回推 changed（removed / changed / views / commands）
  3. 非用户来源的卸载与停用直接回报拒绝原因
  4. 测试用假 client 收集回推帧
- 验收命令：`uv run pytest -q tests/test_extension_manage.py -k host`（期望：全绿）
- 自检：单条失败不影响其它扩展；注册点摘除后 ids() 不再包含它

### T4 obox 编排与增量应用

- 步骤：
  1. app 新增 install_extension / remove_extension / set_extension_enabled，复制包到 incoming 后发消息
  2. _apply_extensions_changed：removed 按 owner 摘视图与注册，changed 挂新视图并刷新应用与设置
  3. 禁用名单写入 config，启动时传给宿主
  4. 测试：构造 changed 载荷，断言视图增删与名单持久化
- 验收命令：`uv run pytest -q tests/test_extension_manage.py -k app`（期望：全绿）
- 自检：摘除当前视图时先切走；重复回推幂等

### T5 摘视图与卸载确认框

- 步骤：
  1. MainWindow.remove_view(view_id)：从栈里移除、删 rail 按钮、清引用
  2. confirm_dialog.py：标题、说明、确认/取消，复用浮层面板的对象名
  3. 测试：remove_view 后 view_ids 不含它；确认框点取消返回 False
- 验收命令：`uv run pytest -q tests/test_extension_manage.py -k view`（期望：全绿）
- 自检：移除当前视图后栈回到首页，不崩

### T6 扩展管理扩展本体

- 步骤：
  1. extensions/management：extension.json（name=extensions、publisher=obox、version=1.0.0、views=[extensions.main]）、extension.py、views/main.oml、i18n.json、main.svg
  2. 页面：安装按钮、搜索框、卡片列表（名称/作者/版本/来源/状态），用户来源卡片带卸载与禁用
  3. extension.py 实现 filter_extensions 与事件处理（安装、卸载、启停、搜索）
- 验收命令：`uv run pytest -q tests/test_extension_manage.py -k filter`（期望：全绿）
- 自检：清单通过 check_extension.py；卡片与 App 页视觉一致

### T7 端到端测试

- 步骤：
  1. 用 scripts/pack_extension.py 把一个最小测试扩展打成本地 .oix
  2. 测试：安装后视图与卡片出现、卸载后消失、禁用后不激活且重启仍在名单
- 验收命令：`uv run pytest -q tests/test_extension_manage.py`（期望：全绿）
- 自检：用临时目录，不污染工程内的 extensions/

### T8 界面验证场景

- 步骤：
  1. verify_ui 增管理页场景：打开「扩展」、截图、断言卡片数 ≥ 内置扩展数
  2. 安装一个临时 .oix 后断言侧栏多入口、卡片出现；卸载前把确认框打桩为直接确认，卸载后断言消失
- 验收命令：`uv run python scripts/verify_ui.py --theme light` 与 `--theme dark`（期望：0 失败）
- 自检：截图编号连续；临时包在 finally 里清理

### T9 扩展开发技能同步

- 步骤：
  1. obox-ext-dev 的 references 补控制消息、管理页写法、禁用名单与来源判断
  2. 跑 check_all
- 验收命令：`uv run python .agents/skills/obox-test/scripts/check_all.py`（期望：退出码 0）
- 自检：文档与 obox/api/extensions.py 的字段逐字一致

### T10 重编与全量验证

- 步骤：
  1. 关闭 obox，重编两套主题（管理扩展不需要 pyd，但主题没变也走一次）
  2. 全量 pytest 与两套 verify
- 验收命令：`uv run python scripts/build_theme.py light dark && uv run pytest -q && uv run python scripts/verify_ui.py --theme light && uv run python scripts/verify_ui.py --theme dark`（期望：全绿）
- 自检：pyd 时间戳为本次；临时扩展目录已清理

## 测试策略

TDD：每任务先写失败测试再实现；端到端用临时目录的 .oix，不污染工程扩展目录。

## 执行顺序

1. T1 ∥ T2 ∥ T5
2. T3
3. T4
4. T6
5. T7
6. T8 ∥ T9
7. T10

## 覆盖检查

- 扩展管理：T1、T4、T5、T6、T8
- 扩展安装：T1、T2、T3、T4、T7、T8、T9
- 扩展生命周期与上下文注入：T3
- 扩展目录与清单：T4

## 自检（落盘前）

- [x] 每条需求都被至少一个任务覆盖
- [x] 每个任务都有可复制执行的验收命令
- [x] 依赖无环，且同文件任务没有并行
- [x] 方式只取 主 Agent / subagent / 后台
- [x] 模板占位与注释已全部替换