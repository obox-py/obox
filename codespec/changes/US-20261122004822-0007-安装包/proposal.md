---
status: done
---

# obox 安装包 Proposal

## 背景

工程只能在源码目录里用 uv 运行。需要 Windows 上可分发的安装包：安装后双击 obox.exe 即可使用，系统扩展随装但以解压目录形式放在安装目录的 extensions/ 下。

## 已确认的结论

| 问题 | 结论 |
|---|---|
| 安装形态 | Nuitka 编译的 obox.exe（standalone）+ .theme 下的 light 与 dark 两个套件 + extensions/ |
| 系统扩展 | 只随装 app 与 settings，放在 安装目录/extensions 下的 app 与 settings 两个目录，已解压，不是 .oix |
| 安装器 | scripts/build_installer.py 生成 .nsi 并调用 makensis；产物 dist 下的 obox 版本号 setup.exe |
| 权限 | RequestExecutionLevel highest：当前用户安装免提权；所有用户安装校验管理员 |
| 静默 | /CURRENTUSER 与 /ALLUSERS，缺省所有用户 |
| 工具 | 本机需安装 NSIS（makensis），构建脚本检测并提示 |

## 目标

- 一条命令产出安装包：构建 exe → 准备 .theme 与系统扩展 → 生成 .nsi → 调 makensis
- 安装后从安装目录启动即可：主题、字体、系统扩展都能被发现
- 用户数据（配置、已安装扩展、扩展存储）写到 %LOCALAPPDATA%\obox，不污染 Program Files
- 卸载清理程序文件与快捷方式，保留用户数据

## 范围

**做**：Nuitka standalone 构建脚本、安装目录布局、运行期路径解析（安装态与源码态）、系统扩展扫描根、NSIS 脚本模板与构建脚本、安装包实测。

**不做**：代码签名、自动更新、MSI/MSIX、卸载时删除用户数据。

## 需求草案

- 安装目录：obox.exe + Nuitka 运行时文件 + .theme/ + extensions 下的 app 与 settings 两个目录
- 路径解析：安装态 project_root = exe 所在目录；数据根 = %LOCALAPPDATA%/obox；源码态仍用仓库根与 .obox
- 扩展扫描：安装目录 extensions/（系统） + %LOCALAPPDATA%/obox/extensions（用户安装的 .oix） + 源码 extensions/；同名以用户安装优先
- 安装器：MUI2、范围页、目录页、开始菜单与桌面快捷方式、按范围写 HKCU/HKLM 卸载项
- 卸载：按安装范围清理程序文件与对应注册表，快捷方式按范围删除
- 构建脚本：检测 makensis 与 NSIS 安装路径；缺 exe 或主题产物时自动先构建；失败非零退出

## 关键取舍

- Nuitka standalone 而非依赖本机 Python：安装包自包含，代价是体积大、构建慢
- 程序目录与数据目录分离：Program Files 只读，用户数据与 .oix 安装落在 LOCALAPPDATA
- 系统扩展随安装目录分发且已解压：启动即用，不经过安装步骤
- 单包同时覆盖两种范围：避免维护两份安装器，权限差异由范围页与管理员校验处理

## 与基线的冲突

- 现状 project_root 固定为源码根、配置固定 .obox/；安装态需要区分程序目录与数据目录
- 扩展扫描根从 2 个变 3 个，加载优先级需要在规格里写清
- 新增构建产物 dist/obox-*-setup.exe 与构建脚本

## 假设

- 目标机 64 位 Windows 10+，不预装 Python
- 安装到 Program Files 需要管理员权限；用户数据在 LOCALAPPDATA 可写
- NSIS 使用官方发行版（含 MUI2）