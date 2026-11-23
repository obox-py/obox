<!--
============================================================
README 模板 · 使用说明（HTML 注释，渲染时不可见，可整段删除）
1. 全局替换所有 {{双花括号}} 占位符为你的项目信息
2. 标有「可选」的章节用不上时整节删除，并同步删掉上方目录中对应条目
3. 徽章由 shields.io 提供：把 {{OWNER}} / {{REPO}} 换成 GitHub 用户名与仓库名；
   仓库不在 GitHub 时，按徽章文档替换为对应平台的地址
4. 图片建议放入仓库（如 docs/images/），用相对路径引用，避免外链失效
5. GitHub 会在页面右侧自动生成目录；若不需要手动目录，删除「目录」整节
6. 需要英文版时翻译标题与正文，并在顶部语言切换行互相链接，英文版应该放在docs/README_EN.md
============================================================
-->

# {{PROJECT_NAME}}

> {{一句话简介：一句话说明这个项目是什么、解决什么问题、适合谁使用}}

[![build](https://img.shields.io/github/actions/workflow/status/{{OWNER}}/{{REPO}}/ci.yml?branch=main&label=build)](https://github.com/{{OWNER}}/{{REPO}}/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/{{OWNER}}/{{REPO}})](https://github.com/{{OWNER}}/{{REPO}}/releases)
[![license](https://img.shields.io/github/license/{{OWNER}}/{{REPO}})](./LICENSE)
[![top language](https://img.shields.io/github/languages/top/{{OWNER}}/{{REPO}})](https://github.com/{{OWNER}}/{{REPO}})

简体中文 | [English](docs/README_EN.md)

<!-- 若不需要英文版，删除上面一行 -->

## 目录

- [简介](#简介)
- [功能特点](#功能特点)
- [演示](#演示)
- [技术栈](#技术栈)
- [环境要求](#环境要求)
- [安装](#安装)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [目录结构](#目录结构)
- [常见问题](#常见问题)
- [路线图](#路线图)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [鸣谢](#鸣谢)
- [联系方式](#联系方式)

## 简介

{{PROJECT_NAME}} 是一个 {{项目类型：命令行工具 / 库 / Web 应用 / 桌面端软件 / 服务}}，用于 {{核心用途}}。

它面向 {{目标用户}}，可以 {{核心价值一}}，同时 {{核心价值二}}。与 {{同类方案}} 相比，主要优势是 {{差异点}}。

- 适用场景：{{场景一}}、{{场景二}}
- 不适用场景：{{场景三}}（写清边界，减少误用）
- 延伸阅读：[快速上手](./docs/quickstart.md)、[API 文档](./docs/api.md)、[更新日志](./CHANGELOG.md)

## 功能特点

- **{{功能一}}**：{{它解决了什么问题，带来什么结果}}
- **{{功能二}}**：{{一句话说明价值，而不是罗列实现细节}}
- **{{功能三}}**：{{支持哪些平台或输入输出格式}}
- **{{功能四}}**：{{性能、体积或易用性上的量化亮点，如「1 万条记录解析 < 200ms」}}

<!-- 可选：与同类项目对比
| 能力 | 本项目 | {{项目 A}} | {{项目 B}} |
|---|---|---|---|
| {{能力一}} | 支持 | 支持 | 不支持 |
| {{能力二}} | 支持 | 不支持 | 支持 |
-->

## 演示

![演示截图](docs/images/demo.gif)

> 上图展示：{{这张图/动图演示了哪个核心流程}}。更多示例见 [examples/](./examples)。

<!-- GitHub 不支持直接内嵌视频，建议用 GIF，或把视频上传到 Release 附件后以链接形式给出 -->

## 技术栈

| 类别 | 选型 | 说明 |
|---|---|---|
| 语言 | {{如 TypeScript 5 / Python 3.11 / Rust 1.75}} | {{选择原因}} |
| 框架 | {{如 React 18 / FastAPI / Axum}} | {{承担的角色}} |
| 数据库 | {{如 PostgreSQL 15 / SQLite / Redis}} | {{存储什么数据}} |
| 构建与包管理 | {{如 pnpm / uv / Cargo}} | |
| 测试 | {{如 Vitest / pytest / cargo test}} | {{覆盖范围}} |
| 部署 | {{如 Docker / Kubernetes / Vercel}} | |

## 环境要求

| 依赖 | 版本要求 | 说明 |
|---|---|---|
| {{Node.js}} | ≥ {{18.0}} | {{运行时}} |
| {{Python}} | ≥ {{3.11}} | {{运行时}} |
| {{Docker}} | ≥ {{24.0}} | {{仅容器方式需要}} |

## 安装

### 方式一：包管理器（推荐）

```bash
# 按实际生态保留其中一行
npm install -g {{PACKAGE_NAME}}      # Node.js
pip install {{PACKAGE_NAME}}         # Python
cargo install {{PACKAGE_NAME}}       # Rust
```

### 方式二：从源码安装

```bash
git clone https://github.com/{{OWNER}}/{{REPO}}.git
cd {{REPO}}
{{INSTALL_DEPS_COMMAND}}    # 例：pnpm install / pip install -r requirements.txt / cargo fetch
{{BUILD_COMMAND}}           # 例：pnpm build / make build / cargo build --release
```

### 方式三：Docker

```bash
docker pull {{OWNER}}/{{REPO}}:latest
docker run -p {{HOST_PORT}}:{{CONTAINER_PORT}} {{OWNER}}/{{REPO}}:latest
```

### 验证安装

```bash
{{PROJECT_NAME}} --version
# 期望输出：{{VERSION}}
```

## 快速开始

最简可用示例，复制粘贴即可跑通：

```bash
{{MINIMAL_RUN_COMMAND}}    # 例：{{PROJECT_NAME}} init / npm start / make dev
```

```bash
# 代码调用示例：将「语言」标注与内容替换为你项目的真实写法
{{MINIMAL_CODE_EXAMPLE}}
```

更多用法：[examples/](./examples)、[完整文档 docs/](./docs)。

## 配置说明

<!-- 可选章节：无配置项的项目可整节删除 -->

复制模板文件后按需修改：

```bash
cp .env.example .env
```

| 变量名 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `{{VAR_1}}` | 是 | 无 | {{用途，以及填写格式}} |
| `{{VAR_2}}` | 否 | `{{默认值}}` | {{不填时的行为}} |

## 目录结构

```text
{{REPO}}/
├── src/                  # 源码
│   ├── {{main 文件}}      # {{入口}}
│   └── {{模块目录}}/      # {{职责}}
├── tests/                # 测试
├── docs/                 # 文档与图片
├── examples/             # 示例代码
├── .env.example          # 环境变量模板
├── {{package.json}}      # {{依赖与脚本定义}}
├── LICENSE
└── README.md
```

## 常见问题

<!-- 可选章节：项目早期可整节删除 -->

<details>
<summary>{{问题一：安装时提示 xxx，怎么办？}}</summary>

{{原因分析与解决步骤，尽量给出可直接执行的命令}}

</details>

<details>
<summary>{{问题二：运行时出现 xxx 报错？}}</summary>

{{排查顺序：日志位置 → 常见原因 → 对应配置项}}

</details>

<details>
<summary>{{问题三：如何升级 / 卸载？}}</summary>

{{对应命令}}

</details>

## 路线图

<!-- 可选章节 -->

- [x] {{已完成，如 v1.0 基础能力}}
- [ ] {{进行中，如 v1.1 支持 Windows}}
- [ ] {{计划中，如 v2.0 插件体系}}

需求与排期以 [Issues](https://github.com/{{OWNER}}/{{REPO}}/issues) 为准，欢迎投票或补充。

## 贡献指南

欢迎一切形式的贡献：提 Issue、补文档、加测试、提 PR。

1. Fork 并克隆仓库到本地
2. 新建分支：`git checkout -b feat/your-feature`
3. 提交前确保检查与测试全部通过：
   ```bash
   {{LINT_COMMAND}}    # 例：pnpm lint / ruff check . / cargo clippy
   {{TEST_COMMAND}}    # 例：pnpm test / pytest / cargo test
   ```
4. 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)，例如 `feat: 支持自定义配置文件路径`
5. 向 `main` 分支发起 Pull Request，在描述中关联对应 Issue

更细的代码风格与协作流程见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 许可证

本项目基于 [{{LICENSE}}](./LICENSE) 协议开源。{{如需商业授权，请联系 {{CONTACT_EMAIL}}。}}

## 鸣谢

- [{{依赖或灵感来源一}}]({{链接}}) —— {{在本项目中承担的作用}}
- [{{依赖或灵感来源二}}]({{链接}}) —— {{在本项目中承担的作用}}

感谢所有 [Contributors](https://github.com/{{OWNER}}/{{REPO}}/graphs/contributors) 的付出。

## 联系方式

- 问题与建议：[Issues](https://github.com/{{OWNER}}/{{REPO}}/issues)
- 邮箱：{{CONTACT_EMAIL}}
- 其他渠道：{{社区、群聊或社交媒体}}
