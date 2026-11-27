---
status: done
---

# Tasks

## 任务清单

| ID | 任务 | 方式 | 涉及文件 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | exe 路径解析 | 主 Agent | obox/runtime.py | 安装版程序目录定位 | - | program_dir=exe 父目录 | 完成 |
| T2 | 回归测试 | 主 Agent | tests/test_install_path.py | 安装版程序目录定位 | T1 | 伪造 exe 用例通过 | 完成 |
| T3 | 文档与门禁 | 主 Agent | README、docs/arch | 安装版程序目录定位 | T2 | 两绑定 pytest、check_all 通过 | 完成 |

## 任务详情

### T1 exe 路径解析
- 步骤：新增 executable_path；is_installed 识别非 python 可执行文件；resolve 优先 exe 父目录
- 验收：tests/test_install_path.py

### T2 回归测试
- 步骤：伪造 obox.exe；断言 system_extensions
- 验收：pytest 7 passed

### T3 文档与门禁
- 验收：check_all、verify light

## 测试策略

单测覆盖源码态与安装态；真实安装包另做冒烟。

## 自检

- [x] 需求有任务覆盖
- [x] 验收可执行
- [x] 依赖无环
