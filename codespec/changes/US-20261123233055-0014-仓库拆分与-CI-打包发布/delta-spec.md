---
status: done
---

# 仓库拆分与 CI 打包发布 Spec Delta

## Purpose

把工程拆成可独立发版的仓库，用 GitHub Actions 在 Windows x64 与 ARM64 上编译安装包与扩展 oix，并让宿主按安装目录与用户目录两处加载主题与扩展。

## ADDED Requirements

### Requirement: 仓库与发布流程

组织 SHALL 维护三个仓库：obox（主程序、系统扩展、系统主题源码）、rdp（远程桌面用户扩展）、webapp（网页应用用户扩展）。所有改动 SHALL 经分支与 Pull Request 合并；PR 上 SHALL 运行测试与打包冒烟；打 tag（v 开头）SHALL 构建并上传发布产物到 GitHub Release。

#### Scenario: PR 走检查

- **WHEN** 向任一分库提交 Pull Request
- **THEN** CI 运行 pytest 与对应打包冒烟，通过后才允许合并

#### Scenario: tag 出 Release

- **WHEN** 在主仓或扩展仓打 v1.2.3 形式的 tag
- **THEN** CI 构建对应产物并上传 Release

### Requirement: 运行时资源目录

宿主 SHALL 从两个位置加载主题与扩展：安装目录下的 themes/ 与 extensions/，以及用户数据目录下的 themes/ 与 extensions/。两处同名时 SHALL 以用户数据目录为准；安装目录缺失时 SHALL 仍能用用户目录启动。

#### Scenario: 系统主题预装

- **WHEN** 安装包安装到本机并首次启动
- **THEN** 设置页的主题列表包含 light 与 dark，来自安装目录 themes/

#### Scenario: 用户主题覆盖

- **WHEN** 用户在数据目录 themes 下放入同名主题
- **THEN** 列表只出现一份，加载的是用户目录里的实现

#### Scenario: 用户扩展与系统扩展并存

- **WHEN** 数据目录 extensions 下安装了 rdp，安装目录 extensions 下有 app、settings、management
- **THEN** 启动后四类扩展都可用，rdp 出现在应用页

## MODIFIED Requirements

### Requirement: 界面套件清单与加载

改自基线「界面套件清单与加载」：扫描范围扩为两处目录。

obox SHALL 从安装目录 themes/ 与数据目录 themes/ 扫描主题套件；套件仍是含 theme.json 与 pyd 的目录，按名字去重、用户目录优先；加载时校验清单与样式能力，失败保留当前套件。

#### Scenario: 两处扫描合并

- **WHEN** 安装目录有 light、dark，用户目录有 my-theme
- **THEN** 主题列表为 light、dark、my-theme

### Requirement: 构建与 pyd 产物

改自基线「构建与 pyd 产物」：补架构与系统资源打包。

构建 SHALL 支持 x86_64 与 ARM64 两种目标；安装包 SHALL 包含编译后的主程序、themes/ 下的 light 与 dark 编译目录、extensions/ 下的系统扩展编译目录（extension.pyd 形式）。用户扩展的 oix SHALL 按架构分别产出，包内入口为 extension.pyd。

#### Scenario: x64 安装包

- **WHEN** 在 x64 runner 上执行发布构建
- **THEN** 产出带 x64 后缀的安装包，内部 themes 与 extensions 目录齐全

#### Scenario: arm64 安装包

- **WHEN** 在 arm64 runner 上执行发布构建
- **THEN** 产出带 arm64 后缀的安装包，内容结构与 x64 一致

### Requirement: 扩展目录与清单

改自基线「扩展目录与清单」：补系统扩展来源与按架构安装。

obox SHALL 同时加载安装目录 extensions/ 下的系统扩展与数据目录 extensions/ 下的用户扩展；扩展清单格式不变。扩展管理安装 oix 时 SHALL 按当前进程架构选择 x64 或 arm64 包，安装后立即激活；目录内的 extension.pyd 优先于源码。

#### Scenario: 安装对应架构

- **WHEN** 在 ARM64 机器上安装 rdp 的 oix
- **THEN** 选择 arm64 包，加载其中的 extension.pyd

#### Scenario: 系统扩展随安装包

- **WHEN** 全新安装后首次启动
- **THEN** 应用、设置、扩展管理三个系统扩展已激活，无需安装

## Impact

- 运行期资源路径变化：主题与扩展各有两个来源目录，重名优先级明确
- 构建产物结构变化：安装包包含 themes/ 与 extensions/ 编译目录；扩展仓按架构产 oix
- 发布流程从本地打包变为 tag 驱动的 CI
- 现有源码模式（开发时 .theme 与 extensions/）需要兼容：开发目录仍可直接运行
