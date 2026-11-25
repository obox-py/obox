---
status: done
---

# Tasks

## 拆分方式

按可验证增量：双源目录、按架构安装、构建脚本与安装包、主仓 CI、两个扩展仓、远端建仓与 PR、文档与验收。

## 任务清单

| ID | 任务 | 方式 | 涉及文件 / 模块 | 对应需求 | 依赖 | 完成判据 | 状态 |
|---|---|---|---|---|---|---|---|
| T1 | 主题双源扫描 | 主 Agent | obox/runtime.py、obox/ui/kit.py、obox/app.py、tests/test_theme_paths.py | 运行时资源目录、界面套件清单与加载 | - | 两目录合并、用户优先、源码态回退 .theme | 待办 |
| T2 | 按架构安装 oix | 主 Agent | obox/extensions/host.py、tests/test_extension_arch.py | 扩展目录与清单 | - | 文件名后缀与进程架构匹配才安装 | 待办 |
| T3 | 构建脚本与安装包 | 主 Agent | scripts/build_theme.py、build_exe.py、build_installer.py、installer/obox.nsi | 构建与 pyd 产物 | - | 产物含 themes/ 与 extensions/，文件名带架构 | 待办 |
| T4 | 主仓 CI | 主 Agent | .github/workflows/build.yml | 仓库与发布流程 | T3 | PR 跑测试，tag 出 x64/arm64 包并上传 Release | 待办 |
| T5 | rdp 独立仓 | 主 Agent | extensions/rdp/**、extensions/rdp/.github/workflows/build.yml | 仓库与发布流程、构建与 pyd 产物 | T2 | 本地打包出双架构 oix，workflow 就绪 | 待办 |
| T6 | webapp 独立仓 | 主 Agent | extensions/webapp/**、extensions/webapp/.github/workflows/build.yml | 同上 | T2 | 同上 | 待办 |
| T7 | 建仓与 PR | 主 Agent | GitHub API | 仓库与发布流程 | T4,T5,T6 | 三仓有初始提交与 PR，CI 触发 | 待办 |
| T8 | 文档与验收 | 主 Agent | README.md、docs/arch.md、.agents/skills/obox-test/** | 全部 | T7 | 构建与安装说明齐备，check_all 通过 | 待办 |

## 任务详情

### T1 主题双源扫描
- 步骤：runtime 提供目录列表；kit.scan_themes 接受多目录去重；app 用合并结果
- 验收：`uv run pytest -q tests/test_theme_paths.py`

### T2 按架构安装 oix
- 步骤：宿主安装前读取文件名后缀与进程架构比对，不匹配则拒绝
- 验收：`uv run pytest -q tests/test_extension_arch.py`

### T3 构建脚本与安装包
- 步骤：主题产物放 themes 下按套件名命名的目录，系统扩展编译进 extensions/，NSIS 带上两个目录
- 验收：`uv run python scripts/build_installer.py --arch x64`（本地产物目录检查）

### T4 主仓 CI
- 步骤：PR 跑 pytest；tag 触发 matrix 构建与 Release 上传
- 验收：workflow 语法检查 + PR 运行结果

### T5 rdp 独立仓
- 步骤：复制扩展目录、加 pack 脚本与 workflow，本地出双架构 oix
- 验收：`uv run python scripts/pack_extension.py extensions/rdp --arch x64`

### T6 webapp 独立仓
- 同上
- 验收：`uv run python scripts/pack_extension.py extensions/webapp --arch arm64`

### T7 建仓与 PR
- 步骤：API 建三个仓库，推送初始提交与分支，开 PR
- 验收：`git remote -v` 与 PR 链接

### T8 文档与验收
- 步骤：README 安装/CI、arch 目录结构、技能同步
- 验收：`uv run python .agents/skills/obox-test/scripts/check_all.py`

## 覆盖检查

- 仓库与发布流程：T4、T5、T6、T7
- 运行时资源目录：T1
- 界面套件清单与加载：T1
- 构建与 pyd 产物：T3、T5、T6
- 扩展目录与清单：T2

## 测试策略

TDD：双源扫描与架构判定先写失败测试；构建产物用目录断言（themes/ 与 extensions/ 存在、文件名含架构）；CI 用 PR 冒烟 + tag 实跑验证。

## 执行顺序

1. T1 ∥ T2
2. T3
3. T4 ∥ T5 ∥ T6
4. T7
5. T8

## 自检

- [x] 需求均有任务覆盖
- [x] 验收命令可执行
- [x] 依赖无环
- [x] 方式只用 主 Agent / subagent / 后台