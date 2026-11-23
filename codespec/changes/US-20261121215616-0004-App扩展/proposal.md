---
status: done
---

# App 扩展 Proposal

## 背景

扩展目前只能通过侧栏图标挂页面。需要「应用」形态：扩展在清单里注册应用，obox 提供应用网格；点卡片后 obox 发消息，扩展回传界面，obox 在独立窗体渲染。

## 参数（已确认）

| 问题 | 结论 |
|---|---|
| 网格列出谁 | 只列声明了 contributes.app 的 |
| 一个扩展几个应用 | 多个，contributes.app 支持对象或数组 |
| 回传形式 | oml 路径或内联片段都允许 |
| 窗口复用 | 由应用声明里的 single 与 persistent 决定 |
| 语言切换 | 已开窗口关闭并按新语言重新请求 |

## app 声明

```json
"contributes": {
  "app": [
    {"id": "demo.notes", "title": "笔记", "single": true, "persistent": true}
  ]
}
```

- id：小写字母开头的点分标识；缺省 `{扩展标识}.app`（数组里缺省 `{扩展标识}.app{序号}`），同一扩展内唯一
- title：卡片与应用窗口标题，缺省用扩展名
- icon：图标路径，**相对扩展的 assets 目录**的 svg；原样显示、不做单色重染（可多彩）；缺省用扩展自身的 icon；越界或缺失时退回扩展图标并记录警告
- single：是否单窗口，缺省 true。true 时同一应用最多一个窗口，再次点击聚焦已有窗口；false 时每次点击新建
- persistent：只在 single 为 true 时有意义，缺省 false。true 时关闭窗口只是隐藏，再次点开恢复原窗口、状态与数值不变；false 时关闭即销毁，再次点开重新向扩展请求界面
- 非单窗口下 persistent 不生效

## 目标

- 主窗口新增「应用」页：网格卡片，左侧图标，右侧两行（应用标题、作者+版本），下方描述。
- 点卡片：按 single/persistent 规则开窗或聚焦；obox 发 APP_OPEN_MSG，扩展回 APP_UI_MSG；obox 渲染 oml 或内联片段。
- 超时、oml 越界、片段装配失败都在窗体内提示。

## 形态（已确认）

- 「应用」页做成**真实扩展** `extensions/app`：name=app、publisher=obox、version=1.0.0，只注册左侧边栏视图，不声明 contributes.app（因此不进应用网格）
- 网格只列**声明了 contributes.app** 的扩展，没声明的都不进
- App 扩展的界面用一个新的 kit 组件 AppGrid：数据由 obox 注入，点击事件回到 App 扩展，App 扩展再用 APP_LAUNCH 请求 obox 开窗

## 需求草案

- 清单注册：contributes.app 支持多应用与 icon/single/persistent
- 模板：o-for、o-if、值绑定、视图 data 与局部更新、生命周期事件
- 应用页：系统扩展 extensions/app，网格由 o-for 渲染，只列声明了 app 的扩展
- 打开：APP_LAUNCH → APP_OPEN_MSG → APP_UI_MSG，窗口按 single/persistent 复用

## 与基线的冲突

- 清单结构扩展：contributes 多一个 app 键
- 装配器从一次性构建变成可局部更新
- 主窗口多一个系统扩展提供的视图

## 应用搜索（本轮追加）

- **匹配范围**：应用标题、扩展描述、作者名；不区分大小写的子串匹配（中文按子串）
- **归属**：过滤由 App 扩展执行。obox 在应用就绪后把完整列表推给 App 扩展（APP_LIST_MSG），扩展缓存；搜索框输入事件回到扩展，扩展过滤后把结果发回 obox（APP_VIEW_DATA_MSG），obox 更新该视图的 apps 数据，o-for 随之局部重建
- **空值**：查询为空时显示全部
- **数据字段**：每条应用带 id、title、description、author、meta、icon，供扩展做匹配与渲染
- **时机**：obox 在扩展激活完成后推送列表；语言切换或扩展变化后重新推送

## 范围

**做：** 多应用声明与校验、应用元数据下发、应用网格、开窗与复用/持久化、界面回传渲染、Image 组件与 Text 字号、演示扩展、测试。

**不做：** 应用市场、跨扩展权限、窗口拖拽排序、应用图标单独配置（先用扩展图标）。

## 关键取舍

- 网格页由 obox 用 kit 组件组装，事件回到 obox 自己处理。
- 持久化靠保留窗口对象（隐藏而非销毁）实现，不做状态序列化。
- 内联片段与 oml 共用同一条装配与翻译通路，只是来源不同。

## 假设

- 同一扩展的多个 app id 互不相同；重复时后一个注册失败并记录。
- 语言切换时已开窗口全部关闭重建，扩展需能重复响应打开消息。
