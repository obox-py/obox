---
status: done
---

# 设置与侧栏容器 Delta Design

## Context

视图容器是 main 与 bottom；主窗口中部是 rail + 全宽视图栈。本轮把 main 改为 sidebar 语义，并新增设置扩展与扩展配置贡献。

## Scope

容器重命名与迁移、设置扩展、配置贡献与读写、设置搜索；不含多用户、导入导出、工作区级覆盖。

## Changes

| 模块 | 改动 | 需求 |
|---|---|---|
| obox/ui/main_window.py | 容器常量改为 sidebar/bottom，add_view 默认 sidebar | 主界面三段布局 |
| obox/app.py | 挂载只认 sidebar/bottom；设置扩展数据注入、SETTINGS_SET 处理、配置写入与即时应用 | 设置扩展、设置读写 |
| obox/extensions/manifest.py | 视图容器白名单 sidebar/bottom；新增 contributes.configuration 校验 | 主界面三段布局、扩展配置贡献 |
| obox/api/settings.py | 新增 SETTINGS_LIST 与 SETTINGS_SET 消息 | 设置读写 |
| extensions/{app,demo,gallery} | 清单 container 从 main 改为 sidebar | 主界面三段布局 |
| extensions/settings | 新增系统扩展：清单、i18n、视图、过滤与提交 | 设置扩展、设置搜索 |

## 决策

- 直接删除 main 并让校验报错，避免新旧容器并存造成语义漂移
- 设置值扁平存进 config.json 的 settings 段，键为 {扩展标识}.{属性名}，扩展后续可读
- 设置页数据由 obox 汇总推送（SETTINGS_LIST），分类与条目按 type 映射到 Switch/Input/Select
- 搜索在设置扩展内完成，回注视图数据（沿用视图数据通路）

## Baseline Diff

| 基线文件 | 章节 | 变为什么 |
|---|---|---|
| codespec/specs/spec.md | 主界面三段布局 | 容器语义改为 sidebar/bottom，明确拒绝 main |
| codespec/specs/design.md | D21 容器语义与设置 | 新增决策 |
| docs/arch.md | 分层与决策表 | 补设置扩展与容器 |
| README.md | 扩展开发、目录结构 | 容器改名与设置扩展说明 |

## Risks / Rollback

| 风险 | 应对 |
|---|---|
| 旧扩展清单写 main | 校验失败并提示，迁移四个内置扩展 |
| 配置写坏 | 写入前读旧文件，失败保留旧值并回报 |
| 设置控件类型有限 | 只支持 bool/string/enum，文档标注 |
