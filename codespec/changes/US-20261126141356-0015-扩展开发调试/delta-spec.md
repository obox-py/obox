---
status: done
---

# 扩展开发调试 Spec Delta

## Purpose

让开发者在本地已安装的 obox 上加载扩展开发目录并用 VS Code 断点调试，不经过 .oix 安装。

## ADDED Requirements

### Requirement: 开发扩展加载

obox SHALL 支持 --dev-extension PATH（可重复）与 DEV_EXTENSION_ADD/REMOVE 消息，把开发目录作为独立来源加载；开发目录 SHALL 不复制到安装目录、不写 disabled 配置，移除后不残留。路径必须含合法 extension.json。开发目录 SHALL 写入配置 dev_extensions，下次启动自动加载。

#### Scenario: 启动时加载开发目录
- **WHEN** 执行 obox --dev-extension D:\work\hello
- **THEN** 扩展列表出现 hello（origin=dev），不产生安装目录副本

#### Scenario: 运行中移除
- **WHEN** 发送 DEV_EXTENSION_REMOVE
- **THEN** 该扩展被停用并从配置移除，其它扩展不受影响

### Requirement: 断点调试

obox SHALL 支持 --debug 与 --debug-port，扩展宿主以 debugpy 在 127.0.0.1:端口 监听并等待 VS Code attach；仓库 SHALL 提供 .vscode/launch.json，至少包含「attach 扩展宿主」与「launch obox 并加载开发扩展」两种配置。debugpy SHALL 属于开发依赖，不进入发布包。

#### Scenario: VS Code 断点命中
- **WHEN** 以 --debug 启动 obox，VS Code 用 attach 配置连上端口，并在开发目录 extension.py 打断点
- **THEN** 命中 breakpoint，可单步与查看变量

### Requirement: 开发目录热重载

obox SHALL 监听开发目录内文件变化，变化后自动重启扩展宿主并重新激活；--no-dev-reload 可关闭。

#### Scenario: 保存即生效
- **WHEN** 修改开发目录里的 extension.py 并保存
- **THEN** 宿主重启，开发扩展重新激活，界面更新

## MODIFIED Requirements

### Requirement: 扩展目录与清单

改自基线「扩展目录与清单」：扫描来源增加 dev。

扫描顺序 SHALL 为 安装目录、系统目录、源码目录、开发目录；dev 来源只来自 --dev-extension 与配置，同名时仍以用户安装优先，但 dev 与已安装同 id 时 SHALL 以 dev 覆盖并记录日志。

#### Scenario: 开发覆盖安装
- **WHEN** 已安装 hello 同时以 dev 加载同名目录
- **THEN** 使用 dev 目录的实现，列表标记 dev

## Impact

- CLI、配置、宿主参数与扫描来源各增加一处
- debugpy 只在 dev 依赖，安装包不带
- 扩展管理需识别 origin=dev（只显示、不移除安装状态）
