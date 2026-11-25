---
status: done
---

# Review

## 评审包

| 项目 | 内容 |
|---|---|
| 变更范围 | obox-py 三仓（obox/rdp/webapp）、双源主题与扩展目录、oix 按架构安装、构建脚本打包 themes/ 与编译后的系统扩展、CI 矩阵与 Release |
| 对应需求 | 仓库与发布流程、运行时资源目录（ADDED）；界面套件清单与加载、构建与 pyd 产物、扩展目录与清单（MODIFIED） |
| 验证证据 | 三仓 v1.0.0 Release：obox x86_64 44.3MB / arm64 35.4MB；rdp、webapp 各 x86_64/arm64 两个 oix；本地 pytest 301 passed；安装暂存目录含 themes/light、themes/dark 与 extensions/{app,settings,management}/extension.pyd |

## 意见清单

| ID | 档位 | 位置 | 问题 | 证据 | 结论 |
|---|---|---|---|---|---|
| R1 | 一般 | CI | 首次运行 7 处失败：host 导入语法、runtime 环境变量、UTF-8 控制台、缺 NSIS、PowerShell 变量插值、Release 权限、测试缺主题 | 运行日志 | 接受 |
| R2 | 一般 | 安装包 | 旧构建把 .theme 与源码扩展塞进安装目录（处理：改为 themes/ 编译目录与 extensions/ pyd 目录） | build_installer 暂存结构 | 接受 |
| R3 | 一般 | 主仓 | extensions/rdp 与 extensions/webapp 仍留在主仓，与独立仓重复（处理：待移出，安装包已不包含） | 目录对比 | 部分接受 |
| R4 | 建议 | 发布流程 | 实际使用直接 push + tag，没有走 PR（处理：后续改动可补 PR 流程） | git 历史 | 部分接受 |
| R5 | 建议 | ARM | windows-11-arm 可用，两个包均产出；Pyside6 6.12 win_arm64 轮子正常 | CI 结果 | 接受 |

## 回归

- 三仓 CI 全绿：test + package(x86_64/arm64) + release
- 本地：`uv run pytest -q` 301 passed；安装暂存结构人工核对
- Release 资产核对：obox 两个 exe，rdp/webapp 各两个 oix

## 结论

- 严重：剩余 0 条
- 一般：R1、R2 接受；R3 部分接受（待移出副本）
- 建议：R4 部分接受；R5 接受
