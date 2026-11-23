---
status: done
---

# Tasks

## 拆分方式

按「打包 → 安装 → 加载 → 测试 → 文档」五段切，每段可独立验证；打包与加载可并行开发，最后端到端联调。

## 全局约束

- 不改扩展 API（activate/deactivate/context）与消息协议。
- .oix 只是 zip，不得引入自定义二进制容器。
- 解压必须校验成员路径，禁止写出安装目录。

## 任务清单

| ID | 任务 | 方式 | 涉及文件 / 模块 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | import 图分析与 pyd 编译 | 主 Agent | `scripts/pack_extension.py` | 扩展打包产物 | - | 给定扩展目录能列出全部本地模块并逐个产出 pyd | 完成 |
| T2 | zip 打包与产物命名 | 主 Agent | `scripts/pack_extension.py` | 扩展打包产物 | T1 | dist 下产出 {名称}.{作者}.{版本}.oix，条目结构正确 | 完成 |
| T3 | oix 安装解压 | 主 Agent | `obox/extensions/loader.py` | 扩展安装 | - | .obox/extensions 下的 oix 被解压到同名目录，覆盖旧目录 | 完成 |
| T4 | 双根扫描与清单入口 | 主 Agent | `obox/extensions/loader.py`、`obox/extensions/manifest.py` | 扩展目录与清单 | T3 | 两个根下的扩展都被识别；入口允许 pyd | 完成 |
| T5 | pyd 入口加载与搜索路径 | 主 Agent | `obox/extensions/host.py` | pyd 入口加载与模块搜索路径 | T4 | 安装目录扩展被激活；同目录模块可 import | 完成 |
| T6 | 测试与端到端 | subagent | `tests/` | 全部 | T2、T5 | 单测覆盖三条路径；打包后安装可被 obox 加载 | 完成 |
| T7 | 文档与基线回填 | 主 Agent | `README.md`、`docs/arch.md` | 全部 | T6 | README 有打包与安装说明；arch 补目录 | 完成 |

## 任务详情

### T1 import 图分析与 pyd 编译

- 步骤：
  1. 用 ast 解析入口文件，收集 import 语句，只保留能解析到扩展目录内文件的模块
  2. 递归展开，得到可达文件集合；入口恒在集合内
  3. 逐文件调用 Nuitka --module 编译为同名 pyd，产物收集到临时目录
- 验收命令：`uv run python scripts/pack_extension.py extensions/demo --dry-run`（期望：打印可达文件列表）
- 自检：循环 import 不死循环；不存在的本地模块不报错

### T2 zip 打包与产物命名

- 步骤：
  1. 读 extension.json 取 name、publisher、version
  2. 把 pyd、清单、assets 全部写进 zip，路径以 zip 根为基准
  3. 产物写 dist/{name}.{publisher}.{version}.oix；失败清理临时目录
- 验收命令：`uv run python scripts/pack_extension.py extensions/demo`（期望：dist/demo.obox.0.1.0.oix 存在）
- 自检：zip 里没有 .py；assets 子目录完整

### T3 oix 安装解压

- 步骤：
  1. 扫描 .obox/extensions 下的 *.oix
  2. 校验 zip 成员路径不得越出目标目录
  3. 清空同名目标目录后解压，记录安装日志
- 验收命令：`uv run pytest -q tests/test_install.py`（期望：通过）
- 自检：恶意 ../ 成员被拒绝

### T4 双根扫描与清单入口

- 步骤：
  1. scan_extensions 接受多个根，去重后返回
  2. manifest 校验：入口为 extension.py 或 extension.pyd 且文件存在
- 验收命令：`uv run pytest -q tests/test_manifest.py tests/test_loader_roots.py`（期望：通过）
- 自检：同名扩展出现在两个根时以安装目录为准并告警

### T5 pyd 入口加载与搜索路径

- 步骤：
  1. 加载前把扩展目录插入 sys.path
  2. 有 extension.pyd 时用 spec_from_file_location 以 extension 为名加载，否则回退源码
  3. 记录模块重名告警
- 验收命令：`uv run pytest -q tests/test_host_pyd.py`（期望：通过）
- 自检：pyd 扩展的视图能注册并在界面上出现

### T6 测试与端到端

- 步骤：
  1. 单测覆盖 import 图、zip 结构、安装、扫描、加载
  2. 端到端：打包 demo 的副本→安装→启动 obox→视图出现
- 验收命令：`uv run pytest -q`（期望：全过）
- 自检：打包耗时记录在日志

### T7 文档与基线回填

- 步骤：
  1. README 补打包命令、安装位置、加载顺序
  2. docs/arch.md 补 .obox/extensions 与 dist/
- 验收命令：`python .../check.py --proj . --us US-20261121185654-0003 --baseline-only`（期望：ok）
- 自检：文档与实现一致

## 测试策略

常规：先实现后补测试，每个任务跑自己的验收命令。

## 执行顺序

1. T1
2. T2 ∥ T3
3. T4
4. T5
5. T6
6. T7

## 覆盖检查

- 扩展打包产物：T1、T2
- 扩展安装：T3
- 扩展目录与清单：T4
- pyd 入口加载与模块搜索路径：T5

## 自检（落盘前）

- [x] 每条需求都被至少一个任务覆盖
- [x] 每个任务都有可复制执行的验收命令
- [x] 依赖无环
- [x] 方式只取主 Agent、subagent、后台
- [x] 模板占位符全部替换
