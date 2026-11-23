---
status: done
---

# 设置与侧栏容器 Delta Spec

## ADDED Requirements

### Requirement: 设置扩展

工程 SHALL 提供系统扩展 extensions/settings（name=settings、publisher=obox、version=1.0.0）：它只注册 sidebar 视图；界面仿 VSCode，左侧分类（外观、语言、扩展、关于）、右侧设置项、顶部搜索框；外观与语言修改即时生效，其余设置写入配置。

#### Scenario: 侧栏入口
- **WHEN** obox 启动并激活 settings.obox
- **THEN** 活动栏出现设置图标，点开显示分类与设置项

#### Scenario: 即时生效
- **WHEN** 在设置页切换主题或语言
- **THEN** 主界面立即换主题/语言，选择写入 .obox/config.json

### Requirement: 扩展配置贡献

extension.json SHALL 支持 contributes.configuration：属性表每项声明 type（bool、string、enum）、title、default 与可选 enum；obox 校验后汇总成设置项，随设置视图数据下发给设置扩展；非法类型或重复键被拒绝。

#### Scenario: 贡献被汇总
- **WHEN** 扩展声明两个配置项
- **THEN** 设置页「扩展」分类出现对应控件，默认值来自 default

#### Scenario: 非法贡献
- **WHEN** type 不在白名单或同一扩展键重复
- **THEN** 清单校验失败并指出问题

### Requirement: 设置读写

设置扩展 SHALL 通过 SETTINGS_SET 消息提交修改；obox SHALL 把值写入 .obox/config.json 的 settings 段（键为 {扩展标识}.{属性名}），并对 theme（套件名）与 language（BCP-47）立即应用；写入失败时保留旧值并回报错误。

#### Scenario: 写入并应用
- **WHEN** 设置页把 language 改成 en-US
- **THEN** 界面切换为英文，配置文件里 settings.obox.language 为 en-US

#### Scenario: 写入失败
- **WHEN** 配置文件不可写
- **THEN** 旧值保持生效，设置页收到错误

### Requirement: 设置搜索

设置页 SHALL 提供搜索框：按分类名与设置项标题做不区分大小写的子串过滤，空查询显示全部；过滤在设置扩展内完成，结果回注视图数据。

#### Scenario: 过滤与恢复
- **WHEN** 输入「主题」后清空
- **THEN** 先只显示外观分类，清空后恢复全部分类

## MODIFIED Requirements

### Requirement: 主界面三段布局

obox 主界面由上、中、下三段组成：顶栏左侧显示 obox 图标与名称、右侧提供窗口按钮；中部左侧为只显示图标的活动栏，右侧为侧栏视图区，容器名 sidebar；底部为扩展注册区，容器名 bottom；不再存在 main 容器。

#### Scenario: 扩展注册到侧栏
- **WHEN** 扩展在清单中声明 container 为 sidebar 的视图并带 svg 图标
- **THEN** 活动栏出现该扩展图标，点击后侧栏视图区显示该视图

#### Scenario: 旧清单被拒绝
- **WHEN** 清单仍写 container 为 main
- **THEN** 校验失败并提示改到 sidebar
