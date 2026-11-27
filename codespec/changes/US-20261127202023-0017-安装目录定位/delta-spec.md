---
status: done
---

# 安装目录定位 Spec Delta

## Purpose

安装版重启后系统扩展未加载；改为用 exe 路径推导程序目录。

## ADDED Requirements

### Requirement: 安装版程序目录定位

安装态 obox SHALL 以可执行文件所在目录作为 program_dir；源码态 SHALL 使用仓库根；OBOX_PROGRAM_DIR 仍优先。系统扩展、主题与宿主 --system-dir SHALL 从该 program_dir 派生。判定安装态不得只依赖 sys.frozen 或 __compiled__。

#### Scenario: 安装版找系统扩展
- **WHEN** obox.exe 位于安装目录且同级有 extensions/app、extensions/management、extensions/settings
- **THEN** 启动后宿主扫描到这三个系统扩展并激活

#### Scenario: 伪造 exe 路径
- **WHEN** 测试中把 sys.executable 指向临时目录的 obox.exe
- **THEN** resolve().program_dir 等于该临时目录

## Impact

- 仅改路径解析与测试；目录结构、扩展格式不变
