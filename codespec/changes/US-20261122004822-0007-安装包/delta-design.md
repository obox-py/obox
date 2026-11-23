---
status: done
---

# 安装包 Delta Design

## Context

当前 project_root 由源码位置推导，配置与存储固定在 .obox；扩展扫描两个根。安装版需要程序目录只读、数据目录可写，并多一个系统扩展根。

## Scope

Nuitka standalone 构建、单包安装器（范围页 + 目录页）、路径解析与三根扫描、NSIS 安装体验；不含签名、自动更新、MSI/MSIX。

## Changes

| 模块 | 改动 | 需求 |
|---|---|---|
| scripts/build_exe.py | 新增：Nuitka --standalone 编译 obox 入口，产出 build/obox.dist | 安装包构建 |
| scripts/build_installer.py | 新增：准备安装树、生成 .nsi、调 makensis | 安装包构建 |
| installer/obox.nsi | 新增：MUI2 安装脚本（范围页、目录页、按范围写注册表、自复制卸载） | 安装包构建 |
| obox/runtime.py | 新增：程序目录与数据目录解析（安装态/源码态） | 运行期路径解析 |
| obox/app.py、obox/extensions/supervisor.py、host.py | 修改：使用数据目录与三个扩展根 | 运行期路径解析、系统扩展扫描 |
| obox/extensions/loader.py | 修改：scan_roots 支持三个根与优先级 | 系统扩展扫描 |

## 决策

- 用 Nuitka standalone 而不是打包 Python：目标机不需要 Python；代价是体积大、构建慢
- 数据目录用 LOCALAPPDATA 而不是安装目录：Program Files 无写权限
- 系统扩展随安装目录分发且已解压：启动即可用，不经过 .oix 安装步骤
- 优先级：用户安装 > 系统 > 源码，保证用户可覆盖系统扩展
- 单个安装包 + highest 权限：范围页决定写 HKCU 还是 HKLM；所有用户安装用 HKLM 写入探测管理员权限
- 卸载器复制到临时目录再删除安装目录，避免自删除失败

## Baseline Diff

| 基线文件 | 章节 | 变为什么 |
|---|---|---|
| codespec/specs/spec.md | 新增安装包构建、安装目录布局、运行期路径解析、系统扩展扫描；修改扩展目录与清单 | 追加与替换 |
| codespec/specs/design.md | D23 安装形态与路径 | 追加 |
| docs/arch.md | 部署与目录 | 补安装树 |
| README.md | 安装与运行 | 补安装包用法 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| Nuitka standalone 构建失败或过慢 | 构建脚本分步执行并保留中间产物，失败定位到具体步骤 |
| 安装到 Program Files 后写配置失败 | 数据目录固定 LOCALAPPDATA，启动时创建 |
| 系统扩展被用户覆盖后难排查 | 日志记录优先级与实际加载目录 |
| 安装包体积大 | 只带 light/dark 两套 .theme 与 app/settings 两个扩展 |
| 卸载器位于安装目录导致删不干净 | 复制卸载器到 TEMP，带 /FROMTEMP 再执行，结束后延时清理 |