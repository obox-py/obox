# extension.json 清单

## 必填

| 字段 | 说明 |
|---|---|
| name | 小写字母/数字/连字符，扩展唯一名 |
| version | 语义化版本，如 0.1.0 |
| publisher | 作者标识，与 name 组成扩展 id：`name.publisher` |
| description | 一行描述，应用页会用到 |
| main | 固定 `extension.py` |
| icon | 相对 assets 的 svg |

## contributes

| 键 | 形状 | 说明 |
|---|---|---|
| views | `[{id, name, container, icon?}]` | container 只能是 `sidebar` 或 `bottom`；写 main 启动即报错 |
| commands | `[{command}]` | 需在 context 里注册同名处理函数 |
| app | 对象或数组 | 应用注册：`{id, title, icon, single, persistent}`；icon 相对 assets、原样显示 |
| configuration | `{properties: {key: {type, title, default?, enum?, description?}}}` | type 仅 bool/string/enum；会出现在设置页「扩展」分类 |

## 常见校验错误

- 视图容器只能是 sidebar 或 bottom
- contributes.app 的 id 必须是小写点分标识，且同一扩展内唯一
- configuration 的属性 type 非法、缺 title、enum 默认值不在枚举内

## App 卡片与扩展配置

```json
{
  "name": "webapp",
  "version": "1.0.0",
  "publisher": "chenzhi",
  "main": "extension.py",
  "icon": "main.svg",
  "contributes": {
    "app": { "id": "webapp.app", "title": "网页应用" },
    "configuration": {
      "properties": {
        "profileroot": { "type": "string", "title": "Profile 根目录", "default": "" },
        "limitmb": { "type": "enum", "title": "单站点数据上限", "enum": ["0", "512", "2048"], "default": "2048" }
      }
    }
  }
}
```

- app 卡片点开后，宿主向扩展发 `APP_OPEN_MSG`（payload 有 app_id 与 window_id）；扩展用 `app_ui_message(src, window_id, oml="views/main.oml")` 回页面，oml 是相对扩展目录的路径
- 之后用 `view_data_message(src, "app." + window_id, data)` 注入或更新页面数据；事件仍走 `COMPONENT_EVENT_MSG`
- configuration 的属性名只能是小写字母数字（不能有驼峰或点），设置键为 `<扩展标识>.<属性名>`
- 扩展拿自己的配置：订阅 `EXTENSION_CONFIG_MSG`，payload 是 `{values, defaults}`，键是属性名；宿主在激活后与设置变更后各发一次
