---
status: done
---

# Tasks

## 任务清单

| ID | 任务 | 方式 | 涉及文件 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | CLI 与配置 | 主 Agent | obox/main.py、app.py、pyproject | 开发扩展加载 | - | --dev-extension 可重复、写 config | 完成 |
| T2 | 宿主 dev 来源 | 主 Agent | host.py、supervisor.py | 开发扩展加载、扩展目录与清单 | T1 | dev 目录按 dev 来源激活，origin=dev | 完成 |
| T3 | 运行中增删与清理 | 主 Agent | api/extensions.py、app.py | 开发扩展加载 | T2 | ADD/REMOVE 生效，列表不残留 | 完成 |
| T4 | debugpy 启动 | 主 Agent | supervisor.py、.vscode/launch.json | 断点调试 | T2 | --debug 下 debugpy 监听，launch.json 可 attach | 完成 |
| T5 | 热重载 | 主 Agent | app.py、supervisor.py | 开发目录热重载 | T2 | 开发目录变化触发宿主重启 | 完成 |
| T6 | 测试与文档 | 主 Agent | tests/test_dev_extensions.py、README、ext-dev | 全部 | T4 | 4 条测试通过、文档可照做 | 完成 |

## 任务详情

### T1 CLI 与配置
- 步骤：--dev-extension/--debug/--debug-port/--no-debug-wait/--no-dev-reload；dev_extensions 合并
- 验收：parse_args 测试

### T2 dev 来源
- 步骤：宿主 --dev-dir，activate_all 末尾按 dev 激活并覆盖同 id
- 验收：origin=dev、安装目录无副本

### T3 增删
- 步骤：DEV_EXTENSION_ADD/REMOVE 消息，写配置并重启宿主；状态刷新时清理过期扩展
- 验收：移除后列表消失

### T4 debugpy
- 步骤：debug 时命令行改为 debugpy --listen --wait-for-client
- 验收：单测断言参数；launch.json attach 5678

### T5 热重载
- 步骤：QFileSystemWatcher 监听 dev 目录，防抖重启
- 验收：手工保存观察宿主重启日志

### T6 测试与文档
- 验收：pytest tests/test_dev_extensions.py 4 passed

## 测试策略

TDD：CLI 参数、supervisor 参数、launch.json 结构先写断言；加载/移除用真实宿主进程验证。

## 自检

- [x] 每条需求都有任务覆盖
- [x] 验收命令可执行
- [x] 依赖无环
