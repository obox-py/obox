---
status: done
---

# 安装包 Delta Spec

## ADDED Requirements

### Requirement: 安装包构建

工程 SHALL 只产出一个安装包：scripts/build_installer.py 准备 obox.exe（Nuitka standalone）、.theme 与系统扩展，生成 .nsi 并调用 makensis，产出 dist/obox 版本号 setup.exe；安装包提供范围页（所有用户 / 仅为我安装）与目录页，静默安装用 /ALLUSERS 或 /CURRENTUSER 指定范围、/D 指定目录，缺省所有用户；所有用户安装需管理员权限，当前用户安装不需要。

#### Scenario: 选择范围与目录
- **WHEN** 交互运行安装包
- **THEN** 先选所有用户或当前用户，再在目录页改安装路径，安装到所选位置

#### Scenario: 静默安装
- **WHEN** 运行安装包 /S /CURRENTUSER /D=某目录
- **THEN** 装到该目录、写 HKCU 注册表，无需管理员

#### Scenario: 缺少管理员权限选所有用户
- **WHEN** 非管理员选择所有用户
- **THEN** 提示需要管理员权限并中止，不写文件

#### Scenario: 卸载
- **WHEN** 运行安装目录下的卸载程序
- **THEN** 按安装时范围删除程序文件、快捷方式与 HKCU 或 HKLM 注册表项，保留 %LOCALAPPDATA%\\obox 用户数据

### Requirement: 安装目录布局

安装后的目录 SHALL 为：obox.exe 与 Nuitka 运行时文件、.theme/{light,dark}（pyd 与字体）、extensions/{app,settings}（已解压的系统扩展目录，不是 .oix）；不包含源码与 .py 文件。

#### Scenario: 安装后结构
- **WHEN** 完成安装
- **THEN** 安装目录能直接启动 obox，侧栏出现应用与设置两个系统扩展

### Requirement: 运行期路径解析

obox SHALL 区分程序目录与数据目录：安装态程序目录是 exe 所在目录，数据目录是 %LOCALAPPDATA%\\obox；源码态程序目录是仓库根，数据目录是仓库根的 .obox。配置、扩展存储与用户安装的 .oix 都落在数据目录。

#### Scenario: 安装态写配置
- **WHEN** 在 Program Files 下运行安装版并切换语言
- **THEN** 配置写入 %LOCALAPPDATA%\\obox/config.json，程序目录不被修改

### Requirement: 系统扩展扫描

obox SHALL 扫描三个扩展根：安装目录的 extensions（系统扩展）、数据目录的 extensions（用户安装）、源码 extensions（开发）；同名扩展按「用户安装 > 系统 > 源码」优先，并记录覆盖日志。

#### Scenario: 用户版覆盖系统版
- **WHEN** 用户在数据目录安装了与系统扩展同名的 .oix
- **THEN** 加载用户版，系统版被跳过并记录日志

## MODIFIED Requirements

### Requirement: 扩展目录与清单

扩展 SHALL 可位于安装目录 extensions、数据目录 extensions 与源码 extensions 三处；清单规则不变，容器仍只允许 sidebar 与 bottom。

#### Scenario: 三个根并存
- **WHEN** 三个根各有一个不同扩展
- **THEN** 三者都被加载，侧栏出现三个入口