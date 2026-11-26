---
status: done
---

# 文件与目录选择器 Spec Delta

## Purpose

给扩展补一套文件/目录选择能力：消息式 API + Win11 风格对话框 + 本地与 SSH 浏览，并且按发起窗口模态、异步返回。

## ADDED Requirements

### Requirement: 文件与目录选择器

obox SHALL 支持扩展发起 PICKER_OPEN，参数包含 mode（file 或 dir）、扩展名列表、multi、title、start_path、window_id 与可选 ssh 参数；obox 校验后弹出选择器对话框，用 PICKER_RESULT 返回 paths 或 error。对话框 SHALL 提供快速访问栏、面包屑、搜索、详细信息列表与确认/取消；文件模式按扩展名过滤，目录模式只列目录；multi 为真时返回全部选中项。

#### Scenario: 选择单个文件
- **WHEN** 扩展发起 file 模式、扩展名 txt、multi 为 false
- **THEN** 对话框只显示 txt，确认后 PICKER_RESULT 返回一个绝对路径

#### Scenario: 选择多个目录
- **WHEN** dir 模式且 multi 为 true
- **THEN** 可选中多个目录，结果一次性返回

#### Scenario: 取消
- **WHEN** 用户取消或关闭对话框
- **THEN** 返回空 paths，error 为空

### Requirement: 远端文件浏览

选择器 SHALL 支持通过 SSH 浏览 Windows 与 Linux 远端：参数含 host、port、user、password 或 key_path/passphrase；连接使用 paramiko 的 SFTP，主机指纹自动记录（不弹确认框）；列表与目录切换在后台线程执行，结果返回远端路径与连接标识。

#### Scenario: 浏览远端目录
- **WHEN** 提供合法 SSH 参数并要求 dir 模式
- **THEN** 列表显示远端目录，确认后返回远端路径与 host/user

#### Scenario: 指纹首次确认
- **WHEN** 首次连接未知主机
- **THEN** 弹出指纹确认，拒绝则不建立连接

#### Scenario: 连接失败
- **WHEN** 密码错误或主机不可达
- **THEN** PICKER_RESULT 返回 error，对话框保持可修改参数

### Requirement: 依赖与安装包

运行期依赖为 PySide6、matplotlib 与 paramiko；安装包 SHALL 带上 paramiko 及其依赖，打包脚本不额外裁剪。

#### Scenario: 冻结包可用
- **WHEN** 安装版启动并打开 SSH 选择器
- **THEN** paramiko 可导入，不出现缺少模块错误

## Impact

- 新增两条消息与选择器界面；扩展可异步获取结果
- 新增 paramiko 依赖，安装包体积增加
- 对话框按窗口模态，主窗口与子窗口互不牵连
- 与现有主题、字号规范一致，深色主题同样可用