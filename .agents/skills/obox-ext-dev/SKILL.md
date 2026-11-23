---
name: obox-ext-dev
description: 开发 obox 扩展时使用。覆盖 extension.json 清单、ExtensionContext API、oml 视图与指令、i18n.json、应用注册、.oix 打包；附带可运行的脚手架与校验脚本。
---

# obox 扩展开发

## 何时用

- 新建一个扩展目录（视图、命令、应用、设置贡献）
- 把扩展从 main 容器迁到 sidebar，或补 i18n/打包
- 排查扩展没被激活、视图不显示、事件收不到

## 快速开始

```bash
# 在仓库根执行：生成 extensions/<name> 骨架
uv run python .agents/skills/obox-ext-dev/scripts/scaffold_extension.py hello obox --title 示例

# 校验清单、视图文件与 i18n
uv run python .agents/skills/obox-ext-dev/scripts/check_extension.py extensions/hello

# 运行（扩展放进 extensions/ 即被扫描）
uv run obox
```

## 步骤

1. 目录：`extensions/<name>/extension.json`、`extension.py`、`views/main.oml`、`i18n.json`（可选）、`assets/main.svg`
2. 清单：`main` 固定 `extension.py`；`contributes.views[].container` 只能是 `sidebar` 或 `bottom`（写 main 会被拒绝）
3. 入口：`activate(context)` 里 `register_view`、`register_command`、`register_i18n`；`deactivate` 清理订阅
4. 视图：优先 `views/*.oml`（相对扩展目录），片段内用 o-for/o-if 与 i18n 引用；事件组件写 `on_click` 等属性才会投递
5. 打包：`uv run python scripts/pack_extension.py extensions/<name>`，产物含 extension.pyd、清单、assets、views、i18n.json

## 参考

- `references/manifest.md`：字段、注册点与校验错误
- `references/context-api.md`：context 方法与消息
- `references/oml.md`：标签、指令、绑定、事件
- `references/i18n.md`：i18n.json 格式与 id 规则
- `references/packaging.md`：打包与安装

## 模板

- `templates/extension.json`、`templates/extension.py`、`templates/views/main.oml`、`templates/i18n.json`、`templates/assets/main.svg`

## 边界

- 不改 obox 运行时；需要新能力时走 codespec 变更
- 扩展只能注册自己的 i18n 与应用 id；跨扩展访问通过消息，不直接读文件
