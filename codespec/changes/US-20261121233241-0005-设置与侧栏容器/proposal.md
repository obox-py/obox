---
status: done
---

# 设置与侧栏容器 Proposal

## 背景

当前视图容器是 main 与 bottom。main 的语义不正确：它既不是编辑器区也不是侧栏，只是一个全宽视图区。需要改成 VSCode 式的 sidebar 语义，并补一个设置扩展。

## 目标

把 main 容器改成语义正确的 sidebar，并交付一个仿 VSCode 的设置扩展：分类浏览、搜索过滤、扩展配置贡献、修改即时生效。

## 范围

**做**：容器改名与四个扩展迁移、设置扩展、配置贡献与校验、设置读写与持久化、设置搜索。

**不做**：多用户配置、导入导出、工作区级覆盖、设置版本迁移。

## 已确认的结论

| 问题 | 结论 |
|---|---|
| sidebar 是什么 | 取代 main，成为唯一视图区；rail 仍是活动栏，bottom 保留 |
| 旧扩展怎么办 | 不保留 main：app、demo、gallery 的视图容器全部改为 sidebar，清单校验拒绝 main |
| 设置页形态 | 仿 VSCode：左侧分类、右侧设置项、顶部搜索；分类为外观、语言、扩展、关于 |
| 设置项来源 | 内置项 + 扩展配置贡献（contributes.configuration） |
| 设置搜索 | 要，过滤分类与设置项，空值显示全部 |
| 设置扩展身份 | settings.obox，版本 1.0.0，系统扩展，只注册 sidebar 视图 |

## 需求草案

- 容器：视图容器只允许 sidebar 与 bottom；main 从常量、校验与所有扩展清单中移除
- 设置扩展：sidebar 视图，VSCode 式两栏 + 搜索；外观（主题）、语言（中/英）即时生效
- 扩展配置：清单新增 contributes.configuration（属性表：type、title、default、enum），obox 汇总后推给设置扩展
- 设置读写：设置扩展发 SETTINGS_SET，obox 写入 .obox/config.json；主题与语言立刻应用
- 搜索：设置扩展本地过滤后回注视图数据（复用 VIEW_DATA 通路）

## 非目标

- 不做多用户配置、导入导出、按工作区覆盖
- 不做设置的版本迁移与回滚
- 不做第三方设置 UI 插件

## 关键取舍

- 直接删除 main 而不是兼容并存：语义错误保留只会让新扩展继续写错
- 设置值扁平存在 config.json 的 settings 段：键为 {扩展标识}.{属性名}，便于扩展以后读取
- 扩展配置贡献只支持 bool / string / enum 三种类型，够当前使用；复杂控件留给后续

## 与基线的冲突

- spec 的容器描述需要整节改写（main → sidebar）
- 清单校验新增 configuration 与容器白名单
- 主窗口 layout 需要承载 rail + sidebar 视图栈（bottom 不变）
- 新增消息：扩展配置列表下发、设置写入

## 假设

- 现有四个扩展（app、demo、gallery、settings）在同一轮内完成容器迁移
- 第三方清单若仍写 main，启动时报明确错误而不是静默忽略
