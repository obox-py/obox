---
status: done
---

# 扩展打包 Delta Spec

## ADDED Requirements

### Requirement: 扩展打包产物

工程 SHALL 提供一条命令，分析指定扩展目录内的 import 图，把入口与关联的本地 Python 文件各自编译为同名 pyd，与 extension.json、assets 一起打成 zip，产物为 dist/{名称}.{作者}.{版本}.oix。

#### Scenario: 打包一个合法扩展

- **WHEN** 对包含 extension.json 与 extension.py 的目录执行打包命令
- **THEN** dist 下出现 {名称}.{作者}.{版本}.oix，zip 根目录含 extension.json、extension.pyd、i18n.json（若有）与 assets/、views/

#### Scenario: 漏了清单

- **WHEN** 目标目录没有 extension.json
- **THEN** 命令以非零退出并指出缺少清单，不产出半成品

### Requirement: 扩展安装

obox SHALL 在 .obox/extensions 下发现 .oix 文件时，把它解压到同名目录 {名称}.{作者}；目录已存在时覆盖。

#### Scenario: 安装 oix

- **WHEN** 把 gallery.obox.0.1.0.oix 放进 .obox/extensions
- **THEN** 解压出 gallery.obox 目录，含 extension.json、extension.pyd 与 assets/

#### Scenario: 重复安装

- **WHEN** 同名 .oix 再次放入
- **THEN** 覆盖旧目录并在日志里说明，不残留旧文件

### Requirement: pyd 入口加载与模块搜索路径

obox SHALL 扫描 .obox/extensions 与 extensions/ 两个根，按清单识别扩展；入口存在 extension.pyd 时优先加载 pyd，否则回退 extension.py，并把扩展目录加入模块搜索路径以解析同包依赖。

#### Scenario: 从安装目录加载 pyd 扩展

- **WHEN** .obox/extensions/{id} 下有 extension.json 与 extension.pyd
- **THEN** 扩展被激活，视图与命令正常注册

#### Scenario: 加载时注入搜索路径

- **WHEN** 扩展的 pyd 运行时 import 同目录的其它模块
- **THEN** 能从扩展目录解析到该模块，不报找不到包

#### Scenario: 本地模块重名

- **WHEN** 两个扩展各自带同名本地模块
- **THEN** 先加载者生效，日志记录冲突告警，进程不退出

## MODIFIED Requirements

### Requirement: 扩展目录与清单

obox SHALL 把 extensions/ 与 .obox/extensions 两个根下的目录识别为扩展：目录需含合法 extension.json，入口为 extension.py 或 extension.pyd；.oix 文件在 .obox/extensions 下先解压再扫描。

#### Scenario: 合法源码扩展被识别

- **WHEN** extensions 下存在含 extension.json 与 extension.py 的目录
- **THEN** obox 在扩展列表中列出该扩展

#### Scenario: 合法安装扩展被识别

- **WHEN** .obox/extensions 下存在解压后的目录，含 extension.json 与 extension.pyd
- **THEN** obox 同样列出并激活该扩展


## Impact

- 兼容性：现有源码扩展继续可用；入口解析多一条 pyd 分支。

- 下游影响：task 覆盖打包、安装、加载三块；validation 核对与基线「扩展目录与清单」的替换一致。