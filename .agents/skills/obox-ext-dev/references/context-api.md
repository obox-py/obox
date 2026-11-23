# ExtensionContext

入口 `activate(context)` 拿到的是 `obox.extensions.context.ExtensionContext`。

| 方法 | 用途 |
|---|---|
| `register_view(view_id, source, container="sidebar", title="")` | source 是相对扩展目录的 .oml 路径（也接受内联片段） |
| `register_command(command_id, handler)` | 命令需在清单 commands 里声明 |
| `register_i18n(entry_id, values, name="")` | values 是 BCP-47 到文案，必须含 zh-CN；扩展只能注册自己 |
| `on(msg_id, handler)` | 订阅消息；回调收到 Message |
| `send(message)` | 发送消息，不等待 |
| `request(message, timeout=5.0)` | 返回 Request，可 add_done_callback / await |
| `read_asset(relative_path)` | 读 assets 下文件，越界抛错 |

属性：`extension_id`（name.publisher）、`assets_dir`、`storage_dir`、`subscriptions`。

## 常用消息

```python
from obox.api.component import ComponentModifyMessage
from obox.api.message import COMPONENT_EVENT_MSG, OB_BOX

ComponentModifyMessage(src=context.extension_id, dst=OB_BOX,
                       component_id="demo-title", state_type="text", value="新文案")

context.on(COMPONENT_EVENT_MSG, lambda message: print(message.id, message.event, message.payload))
```

事件只有在 oml 里写了对应 `on_*` 属性时才会投递；payload 里 `value` 对卡片/导航项是 value 属性。

## 运行中的安装、禁用与卸载

obox 自带系统扩展「扩展管理」（目录 extensions/management，清单 name=extensions、publisher=obox），它在页面上完成三件事，扩展本身不需要参与：

| 动作 | 谁做 | 对扩展的影响 |
|---|---|---|
| 安装 .oix | obox 选文件 → 宿主解压并 activate | 激活后视图、应用与设置项立刻出现在各注册点 |
| 禁用 / 启用 | 宿主 deactivate 并摘除注册点，名单写进 .obox/config.json 的 extensions.disabled | 禁用期间不激活；目录与 storage 保留 |
| 卸载 | 宿主 deactivate、删 .obox/extensions/{id} 与 storage | 下次启动不再出现 |

- 来源决定权限：`user`（.obox/extensions 下安装的）可卸载可禁用；`system`（安装目录自带）与 `source`（源码 extensions/）只读
- 同 id 的 .oix 视为覆盖升级：宿主先解压到临时目录，成功才替换，失败保留旧版本
- 被禁用的扩展在宿主启动时直接跳过，不会执行 activate；重新启用后才重新加载
## 锚点滚动

视图里的组件 id 就是锚点。扩展可以要求 obox 平滑滚到某个锚点，并把当前所在锚点回推给扩展：

```python
from obox.api.view import ANCHOR_CHANGED_MSG, VIEW_SCROLL_MSG, view_scroll_message

context.send(view_scroll_message(context.extension_id, "settings.main", "section-about", offset=64, duration=600))

def _on_anchor(message):
    anchor = (message.payload or {}).get("anchor", "")

context.on(ANCHOR_CHANGED_MSG, _on_anchor)
```

- 偏移与时长缺省 64 / 600；锚点只认视图根的直接子组件
- obox 只在当前锚点变化时回推，滚动到顶为第一章节、到底为最后章节
- 视图根的直接子组件写 `sticky="true"` 会成为吸顶条，固定在被滚动内容之上

## App 窗口与配置

```python
from obox.api.app import APP_OPEN_MSG, app_ui_message
from obox.api.settings import EXTENSION_CONFIG_MSG
from obox.api.view import view_data_message

def activate(context):
    state = {"window_id": "", "config": {}}

    def _on_open(message):
        state["window_id"] = message.payload["window_id"]
        context.send(app_ui_message(context.extension_id, state["window_id"], oml="views/main.oml"))
        context.send(view_data_message(context.extension_id, f"app.{state['window_id']}", {"items": []}))

    def _on_config(message):
        state["config"] = dict(message.payload.get("values") or {})

    context.on(APP_OPEN_MSG, _on_open)
    context.on(EXTENSION_CONFIG_MSG, _on_config)
```

- App 窗口的数据通道与普通视图一致，view_id 用 `app.<window_id>`
- 配置值的键是清单里的属性名；未设置的键收到 default
