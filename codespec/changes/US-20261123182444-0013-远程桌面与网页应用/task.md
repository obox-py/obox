---
status: done
---

# Tasks

## 拆分方式

按可验证增量：配置下发、rdp 数据层、rdp 打开链路、rdp 界面、webapp 数据层、webapp 打开链路、webapp 界面、验证与文档各自独立；共 10 个任务。

## 全局约束

- 两个扩展只依赖标准库与 obox.api，不引入第三方依赖
- 系统调用先判断平台，非 Windows 返回提示不抛异常
- 密码只在 DPAPI 密文里出现，不写明文、不进命令行
- 扩展 id 为 rdp.chenzhi 与 webapp.chenzhi；i18n 必含 zh-CN
- 界面沿用 docs/UI.md 的字号与间距

## 任务清单

| ID | 任务 | 方式 | 涉及文件 / 模块 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 扩展配置下发 | 主 Agent | obox/api/settings.py、obox/app.py、tests/test_extension_config.py | 扩展配置贡献 | - | 激活后与变更后各收到一次，只含自己的键 | 完成 |
| T2 | rdp 数据层 | 主 Agent | extensions/rdp/{extension.json,extension.py,i18n.json,assets}、tests/test_extensions_process.py | 远程桌面扩展 | - | 校验/归一/存储/序列化测试全绿 | 完成 |
| T3 | rdp 打开链路 | 主 Agent | extensions/rdp/extension.py、tests/test_extensions_process.py | 远程桌面扩展 | T2 | DPAPI 往返、.rdp 文本、脱离式启动参数正确 | 完成 |
| T4 | rdp 界面 | 主 Agent | extensions/rdp/views/main.oml | 远程桌面扩展 | T3 | 列表 + 搜索 + 新建/编辑 + 打开/删除可用 | 完成 |
| T5 | webapp 数据层与配置 | 主 Agent | extensions/webapp/{extension.json,extension.py,i18n.json,assets}、tests/test_extensions_process.py | 网页应用扩展、扩展配置贡献 | T1 | 校验/归一/配置解析测试全绿 | 完成 |
| T6 | webapp 打开链路 | 主 Agent | extensions/webapp/extension.py、tests/test_extensions_process.py | 网页应用扩展 | T5 | Chrome 探测顺序、启动参数、缺失提示正确 | 完成 |
| T7 | webapp 界面 | 主 Agent | extensions/webapp/views/main.oml | 网页应用扩展 | T6 | 列表 + 搜索 + 表单 + 开关可用 | 完成 |
| T8 | 验证场景 | 主 Agent | scripts/verify_ui.py | 两个扩展 | T4,T7 | 两个 App 打开并截图，两套主题 0 失败 | 完成 |
| T9 | 技能文档同步 | subagent | .agents/skills/obox-ext-dev/** | 扩展开发技能 | T1 | App 卡片与配置读取示例齐全，check_all 通过 | 完成 |
| T10 | 全量验证 | 后台 | tests、scripts/verify_ui.py | 全部 | T8,T9 | pytest 全绿、verify 两套 0 失败 | 完成 |

## 任务详情

### T1 扩展配置下发

- 步骤：
  1. api/settings.py 增 EXTENSION_CONFIG_MSG 与构造函数
  2. app 在 _on_extensions_ready 与 _on_settings_set 后，按扩展前缀发送 values + defaults
  3. 测试：webapp 收到 profileRoot 默认值；改设置后再收到；不含别人的键
- 验收命令：`uv run pytest -q tests/test_extension_config.py`（期望：通过）

### T2 rdp 数据层

- 步骤：
  1. manifest + extension.py：连接归一与校验、connections.json 读写、i18n 注册
  2. 测试：名称唯一、端口范围、归一默认值
- 验收命令：`uv run pytest -q tests/test_extensions_process.py -k rdp`（期望：通过）

### T3 rdp 打开链路

- 步骤：
  1. DPAPI 加解密（ctypes），secrets.json 存 base64 密文
  2. .rdp 文本生成（full address / username / domain / authentication level / prompt for credentials / password 51:b）
  3. 脱离式启动 mstsc；非 Windows 返回提示
- 验收命令：`uv run pytest -q tests/test_extensions_process.py -k rdp`（期望：通过）

### T4 rdp 界面

- 步骤：OML 列表 + 搜索 + 新建/编辑表单 + 打开/删除按钮；事件回扩展
- 验收命令：`uv run pytest -q tests/test_builder.py`（装配不报错），再人工打开卡片

### T5 webapp 数据层与配置

- 步骤：manifest（app + configuration）、站点归一/校验、sites.json、配置消息缓存
- 验收命令：`uv run pytest -q tests/test_extensions_process.py -k webapp`（期望：通过）

### T6 webapp 打开链路

- 步骤：Chrome 探测（注册表 → Program Files → PATH）、参数拼装、脱离启动、缺失提示
- 验收命令：`uv run pytest -q tests/test_extensions_process.py -k webapp`（期望：通过）

### T7 webapp 界面

- 步骤：OML 列表 + 搜索 + 表单（URL、忽略证书开关）+ 打开/删除
- 验收命令：`uv run pytest -q tests/test_builder.py`（装配不报错），再人工打开卡片

### T8 验证场景

- 步骤：verify 打开「远程桌面」与「网页应用」卡片，截图；不发起连接
- 验收命令：`uv run python scripts/verify_ui.py --theme light` 与 `--theme dark`（期望：0 失败）

### T9 技能文档同步

- 步骤：ext-dev 补 contributes.app 与配置读取示例
- 验收命令：`uv run python .agents/skills/obox-test/scripts/check_all.py`（期望：退出码 0）

### T10 全量验证

- 步骤：全量 pytest 与两套 verify
- 验收命令：`uv run pytest -q && uv run python scripts/verify_ui.py --theme light && uv run python scripts/verify_ui.py --theme dark`（期望：全绿）

## 测试策略

TDD：配置下发与两个扩展的纯函数先写失败测试；界面用 Builder 装配断言不报错，交互由 verify 截图确认。

## 执行顺序

1. T1 ∥ T2
2. T3
3. T4 ∥ T5
4. T6
5. T7
6. T8 ∥ T9
7. T10

## 覆盖检查

- 远程桌面扩展：T2、T3、T4、T8
- 网页应用扩展：T5、T6、T7、T8
- 扩展配置贡献：T1、T5
- 扩展开发技能：T9

## 自检（落盘前）

- [x] 每条需求都被至少一个任务覆盖
- [x] 每个任务都有可复制执行的验收命令
- [x] 依赖无环，且同文件任务没有并行
- [x] 方式只取 主 Agent / subagent / 后台
- [x] 模板占位与注释已全部替换