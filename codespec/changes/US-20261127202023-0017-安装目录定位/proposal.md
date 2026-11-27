---
status: done
---

# 安装目录定位 · 用 exe 路径找系统扩展

## 背景

安装版重启后系统扩展没有加载。安装目录里 extensions/{app,settings,management} 存在，但运行期 program_dir 可能按 __file__ 推导；Nuitka 冻结后 __file__ 不是真实的 exe 所在目录，导致 system-dir 指向错误位置，宿主扫不到系统扩展。

## 目标

- 安装态一律用可执行文件所在目录作为 program_dir
- 不依赖 sys.frozen / __compiled__ 这种在各模块里不一定可见的标记
- 源码态仍用仓库根（obox/__init__.py 上两级）
- 系统扩展、主题、宿主 --system-dir 都从同一个 program_dir 派生
- 测试覆盖：把 sys.executable 指向伪造的 obox.exe，断言 program_dir 是其父目录

## 范围

**做：**

- runtime.resolve 增加可执行文件判定：文件名不是 python.exe/pythonw.exe 时用其父目录
- is_installed 同步识别（exe 名、OBOX_INSTALLED、sys.frozen、__compiled__）
- tests/test_runtime.py 增加 exe 路径用例
- README/docs/arch 补安装态定位规则

**不做：**

- 不改安装包目录结构
- 不改扩展扫描优先级
- 不引入新依赖

## 需求草案

1. 运行期 program_dir 在安装态必须等于 obox.exe 的父目录
2. 源码态继续使用仓库根
3. OBOX_PROGRAM_DIR 环境变量仍优先
4. 系统扩展目录 = program_dir/extensions；主题目录 = program_dir/themes 或 .theme
5. 宿主 --system-dir 使用同一 program_dir
6. 单测用伪造 exe 路径验证，不依赖真实安装

## 关键取舍

- 用 exe 文件名判定安装态，比 sys.frozen 在 Nuitka 下更可靠
- 保留环境变量覆盖，便于测试与绿色版
- 只在路径解析层改，不碰扩展加载逻辑

## 与基线的冲突

- 基线只写「安装态用程序目录」，未写如何得到；MODIFIED 运行路径规则

## 假设

- 安装包为 standalone 目录，obox.exe 与 extensions/ 同级
- Nuitka 下 sys.executable 指向 obox.exe
