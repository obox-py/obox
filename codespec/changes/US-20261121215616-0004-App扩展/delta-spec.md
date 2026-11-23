---
status: done
---

# App 扩展 Delta Spec

## ADDED Requirements

### Requirement: 应用注册

扩展 SHALL 在 extension.json 的 contributes.app 里注册一个或多个应用；每一项可声明 id、title、icon、single、persistent：id 缺省 {扩展标识}.app（数组按下标追加序号），icon 是相对 assets 目录的 svg 路径且原样显示、不做单色重染，single 缺省 true，persistent 缺省 false 且仅在 single 为 true 时生效。

#### Scenario: 多应用声明
- **WHEN** 扩展用数组声明两个应用
- **THEN** 两个应用都能被识别，id 互不相同

#### Scenario: 非法声明
- **WHEN** id 不是小写字母开头的点分标识，或同一扩展内 id 重复
- **THEN** 清单校验失败并指出问题

#### Scenario: 图标缺失
- **WHEN** icon 指向的文件不存在或越出 assets
- **THEN** 退回扩展自身图标并记录警告，不影响应用可用

### Requirement: 模板指令与值绑定

OML 与内联片段 SHALL 支持 o-for、o-if 与值绑定：o-for="item in items" 按列表重复元素（作用域内可用 item 与 index），o-if="expr" 按条件渲染；表达式 在文本与属性中绑定数据；表达式支持点路径、length、字面量与 ==、!=、>、<、! 比较；i18n 引用优先解析，未解析的保持原样。

#### Scenario: 列表渲染
- **WHEN** 片段写 o-for="app in apps"，apps 有三项
- **THEN** 渲染三份元素，作用域内 app.title 绑定 与 index 正确

#### Scenario: 条件渲染
- **WHEN** o-if="apps.length" 且列表为空
- **THEN** 该元素不渲染；数据变为非空后出现

#### Scenario: 嵌套作用域
- **WHEN** o-for 内部再嵌套 o-for
- **THEN** 内层能同时访问外层与内层变量

### Requirement: 视图数据与局部更新

扩展注册视图时 SHALL 能提供初始 data；obox SHALL 能注入或更新视图数据，更新时只刷新受影响的部分：文本与属性绑定原地改写，o-for 与 o-if 区域按其容器重建，不重建整棵视图。

#### Scenario: 文本原地更新
- **WHEN** 视图数据里的 title 变化
- **THEN** 对应文本原地改写，其它组件实例保持不变

#### Scenario: 列表变化
- **WHEN** apps 从三项变成两项
- **THEN** 只重建该 o-for 区域，其余视图不动

### Requirement: 视图生命周期

视图 SHALL 在渲染完成、数据更新后与销毁时向所属扩展投递 mounted、updated、unmounted 事件，携带 view_id。

#### Scenario: 挂载与销毁
- **WHEN** 视图被装配并显示，随后切走并销毁
- **THEN** 扩展依次收到 mounted 与 unmounted

### Requirement: 应用页作为系统扩展

应用页 SHALL 由仓库内的真实扩展 extensions/app 提供（name=app、publisher=obox、version=1.0.0）；该扩展只注册左侧边栏视图，不声明 contributes.app，因此不出现在应用网格里；其界面使用 AppGrid 组件，数据由 obox 注入，点击事件回到该扩展后再由 APP_LAUNCH 请求 obox 开窗。

#### Scenario: 侧栏入口
- **WHEN** obox 启动并激活 app.obox
- **THEN** 侧栏出现「应用」图标，点开显示应用网格

#### Scenario: 自身不进网格
- **WHEN** 查看应用网格
- **THEN** 只出现声明了 contributes.app 的扩展，app.obox 本身不在其中

### Requirement: 应用网格

obox SHALL 在主窗口提供「应用」页，用网格卡片列出所有声明了 app 的已激活扩展：卡片左侧图标，右侧两行（应用标题、作者与版本），下方描述；未声明 app 的扩展不出现在此页。

#### Scenario: 卡片内容
- **WHEN** 打开「应用」页
- **THEN** 每个应用一张卡片，图标为声明里的 icon（原样颜色），标题为 title，第二行为作者与版本，下方为扩展描述

#### Scenario: 未声明不出现
- **WHEN** 扩展没有 contributes.app
- **THEN** 应用页没有它的卡片

### Requirement: 打开应用与窗口复用

App 页的卡片由 o-for 遍历 apps 数据生成；点击卡片 SHALL 由 App 扩展发出 APP_LAUNCH（app_id），obox 收到后创建或复用窗口，并向目标扩展发 APP_OPEN_MSG（app_id、window_id）；扩展以 APP_UI_MSG 回传 oml 路径或内联片段；obox 渲染并替换内容。single 为 true 时同一应用最多一个窗口，关闭行为由 persistent 决定；single 为 false 时每次点击新建窗口。

#### Scenario: 单窗口聚焦
- **WHEN** 单窗口应用已打开，再次点击它的卡片
- **THEN** 聚焦已有窗口，不新建

#### Scenario: 持久化恢复
- **WHEN** 单窗口且持久化的应用被关闭后再次打开
- **THEN** 直接显示原窗口与原状态，不重新请求界面

#### Scenario: 非持久化重建
- **WHEN** 单窗口但非持久化的应用被关闭后再次打开
- **THEN** 新建窗口并重新发送 APP_OPEN_MSG

#### Scenario: 多窗口
- **WHEN** single 为 false 的应用被点击两次
- **THEN** 出现两个窗口，各自携带不同的 window_id

#### Scenario: 超时
- **WHEN** 三秒内没有收到 APP_UI_MSG
- **THEN** 窗口显示「扩展未返回界面」

#### Scenario: 内联片段
- **WHEN** APP_UI_MSG 带 html 而不是 oml
- **THEN** obox 直接装配并渲染该片段

### Requirement: 应用搜索

应用页 SHALL 提供搜索框：输入时按应用标题、扩展描述与作者做不区分大小写的子串匹配，过滤网格卡片；查询为空时显示全部；过滤由 App 扩展执行，结果通过 APP_VIEW_DATA_MSG 回注，obox 只接受该视图 owner 发来的消息与已知应用。

#### Scenario: 子串过滤
- **WHEN** 在搜索框输入「笔」
- **THEN** 只保留标题、描述或作者含「笔」的卡片

#### Scenario: 清空恢复
- **WHEN** 清空搜索框
- **THEN** 网格恢复显示全部应用

#### Scenario: 扩展增删后同步
- **WHEN** 运行中新增或卸载某个扩展（.oix 或源码目录变化）
- **THEN** 扩展宿主重启、应用列表重新计算，App 扩展收到新的完整列表并按当前查询重新过滤，卡片随之更新

#### Scenario: 越权与伪造被拒
- **WHEN** 非该视图 owner 发送过滤结果，或结果里含未注册的应用 id
- **THEN** obox 忽略这些条目，界面不变

## MODIFIED Requirements

### Requirement: 扩展目录与清单

清单新增可选 contributes.app，取对象或数组；每项字段为 id、title、icon、single、persistent，校验规则见「应用注册」。

#### Scenario: 旧清单不受影响
- **WHEN** 清单没有 contributes.app
- **THEN** 扩展照常加载，只是不出现在应用网格