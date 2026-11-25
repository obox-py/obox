---
status: done
---

# 仓库拆分与 CI 打包发布

## 背景

当前仓库没有提交历史，也没有远端与 CI；主题从 .theme 目录扫描，扩展从本地目录加载。目标是在 GitHub 组织 obox-py 下建立仓库体系：obox 主仓（含系统扩展与两套系统主题）、每个用户扩展一个独立仓库；用 GitHub Actions 在 Windows x64 与 ARM64 上编译安装包、系统扩展与主题目录、以及用户扩展的 oix；以 PR 方式提交，打 tag 出 Release。

## 目标

- obox-py 下创建仓库：obox（主程序 + 系统扩展 + light/dark 主题源码）、rdp、webapp（用户扩展各一仓）
- PR 流程：改动经分支 + Pull Request 合并，CI 在 PR 上验证、打 tag 出 Release
- Windows x64 与 ARM64 两套安装包；安装包内包含 themes/（Nuitka 编译后的 light、dark 目录）与 extensions/（系统扩展，编译为 pyd 目录）
- 用户扩展仓库各自产出 oix：内部 extension.py 编译为 extension.pyd，按架构出 x64 / arm64 两个包
- 主题不再以 oix 安装：系统主题预装在安装目录 themes/，用户主题目录为数据目录下 themes/，运行时两处都扫描
- 扩展安装仍走扩展管理：用户扩展 oix 可安装、可卸载，安装后立即激活

## 范围

**做：**

- 创建远端仓库与初始提交，按 PR 流程合并
- 运行期目录调整：themes 从「安装目录/themes + 数据目录/themes」扫描；extensions 从「安装目录/extensions + 数据目录/extensions」加载
- 构建脚本：系统主题编译为目录、系统扩展编译为 pyd 目录并随安装包分发；用户扩展打包脚本支持按架构
- 三个仓库的 GitHub Actions：测试、构建（x64/arm64）、tag 触发 Release 上传产物
- 版本与产物命名约定（安装包、oix 带架构后缀）

**不做：**

- 不做主题的市场/在线安装 UI（用户主题目录先支持手动放入）
- 不做代码签名与公证
- 不做 macOS / Linux 产物
- 不在本次改造扩展 API

## 需求草案

1. 组织下建立 obox 仓库，包含主程序、系统扩展（app、settings、扩展管理）与 light/dark 主题源码
2. 建立 rdp 与 webapp 两个独立仓库，各自含完整扩展源码与打包脚本
3. 所有改动通过分支 + PR 提交，PR 上运行 pytest 与打包冒烟；合并后再进入发布
4. 打 tag（v*）时构建 x64 与 ARM64 安装包，并上传到 GitHub Release
5. 安装包目录内包含 themes/light、themes/dark（Nuitka 编译后的目录）与 extensions/（系统扩展 pyd 目录）
6. 用户扩展仓库在 tag 时产出 oix（x64 与 arm64 各一份），oix 内的 extension.py 已编译为 extension.pyd
7. 宿主运行时优先从安装目录找主题与系统扩展，并把数据目录下的 themes/ 与 extensions/ 合并进扫描
8. 扩展管理安装 oix 时按当前架构选择对应包，安装后立即激活

## 关键取舍

- 系统扩展与 obox 同仓：随安装包一起编译，省去运行时下载；用户扩展独立仓：可独立发版、独立安装
- 主题以目录而非 oix 分发：系统主题与安装包同生命周期；用户主题是目录拷贝，避免为样式引入包管理
- 两套架构各出一份 oix：pyd 与架构绑定，不做跨架构 universal 包
- 路径扫描顺序：安装目录在前、用户目录在后，重名时用户目录优先（可覆盖）
- CI 以 tag 为发布闸门：PR 只验证，避免每次提交都产包

## 与基线的冲突

- 基线「目录结构」「数据目录」只描述 .theme 与数据目录下 extensions，需要补安装目录与用户 themes 的扫描顺序
- 基线「扩展安装与卸载」只处理扩展 oix，需要补按架构选择包与系统扩展来源
- 基线「构建与打包」只描述本地 Nuitka 与 NSIS，需要补 arm64、系统扩展与主题目录的打包
- README 的安装与开发说明需要补远端仓库与 CI 用法

## 假设

- 系统扩展范围：extensions/app、settings、management 三个；gallery 与 demo 视为开发样例，不随安装包分发
- ARM64 使用 GitHub 托管 windows-11-arm；若组织不可用，先发 x64 并在 PR 说明
- 两个用户扩展仓库从当前工作区对应目录初始化，保留现有提交前状态
- 远端仓库默认 public，使用 .gitoken 的令牌推送
