---
status: done
---

# 扩展打包 Proposal

## 背景

扩展目前只能以源码目录形式放在 extensions/ 下，连同 .py 一起分发，既不能隐藏实现，也不方便安装。需要一条打包链：把扩展编译成 pyd，连同清单与资产打成一个可分发的 .oix（zip）；obox 侧要能把它解压安装到 .obox/extensions/{名称}.{作者} 并加载。

## 目标

- 打包脚本：分析扩展目录内的 import 图，把 extension.py 与关联的本地 py 各自编成同名 pyd，与 extension.json、assets/ 一起打成 dist/{名称}.{作者}.{版本}.oix。
- 安装：.oix 解压到 .obox/extensions/{名称}.{作者}，清单与资产保持原约定。
- 加载：obox 同时扫描 .obox/extensions 与 extensions/，读取清单后优先加载 extension.pyd，其次 extension.py，并把扩展目录加入模块搜索路径。
- 现有源码扩展的加载方式保持不变。

## 范围

**做：**

- scripts/pack_extension.py：import 图分析、逐文件 Nuitka 编译、zip 打包、产物落 dist/。
- obox 侧：.oix 识别与解压安装、双目录扫描、pyd 入口加载、sys.path 注入。
- 清单校验放宽到入口可以是 extension.pyd。
- 测试与文档（打包、安装、加载、冲突告警）。

**不做：**

- 不做签名与校验和、在线分发与市场、版本升级回滚。
- 不把 obox.api 与第三方库打进包内。
- 不保留 .py 源码（包内只有 pyd）。
- 不做非 Windows 平台。

## 需求草案

1. 打包：指定扩展目录后分析本地 import，编译为同名 pyd，产出 dist/{名称}.{作者}.{版本}.oix；失败非零退出且不留半成品。
2. 包结构：zip 根目录含 extension.json、extension.pyd 与其它本地模块的 pyd、assets/ 全部文件。
3. 安装：.obox/extensions 出现 .oix 时解压到同名目录；目录已存在时覆盖，并在日志里说明。
4. 加载：扫描 .obox/extensions 与 extensions/，按清单识别扩展；入口优先 pyd，其次源码，目录加入 sys.path。
5. 冲突处理：不同扩展的同名本地模块以先加载者为准，记录告警不中断。

## 关键取舍

- 每个本地 py 编成一个同名 pyd，而不是合并成单个 pyd：与「把目录加入搜索路径」的加载方式一致，模块间仍按名字互相 import；否掉合并方案（Nuitka 对非包结构支持差，且不能再按名引用兄弟模块）。
- .oix 就是 zip：扩展名区分用途，内部结构与安装目录一致；否掉自定义二进制容器。
- 双目录扫描：安装目录与开发目录并存，开发流程不被破坏；否掉只扫安装目录。
- 打包不内嵌第三方库：扩展与 obox 共用环境，体积可控；否掉自包含（PySide6 这类带数据文件的库编不进去）。

## 与基线的冲突

- 基线 spec 的「扩展目录与清单」只写了 extensions/ 与 extension.py 入口；本轮增加 .obox/extensions、.oix 安装与 pyd 入口，需要 MODIFIED。
- 基线 design 的 D11 模块布局要补一句安装目录；D3 单宿主进程、D4 消息方向不变。

## 假设

- 扩展本地模块名在全局唯一；冲突时首个加载者生效并记录告警。
- 打包产物与运行环境的 Python 版本绑定（当前 3.12），升级 Python 需重打。
- 解压安装不做原子替换的复杂处理，覆盖即可。
