# 组件契约

## 标签（21）

div、text、button、input、textarea、checkbox、radio、switch、select、slider、tag、table、tabs、modal、notification、flex、card、choice、alert、image、navitem

## 组件类形状

```python
class XxxComponent(Component):
    tag = "xxx"
    supported_states = ("text", "visible")           # 状态名
    state_accessors = {"text": ("text", "set_text")} # 状态 -> (getter, setter)
    supported_events = ("click",)                    # 事件名
    event_methods = {"click": "on_click"}            # 事件 -> on_* 方法

    def build_widget(self, attrs): ...               # 返回 QWidget
    def container_layout(self): ...                  # 容器组件才需要
```

- states 与 accessors 的键必须一致；events 与 event_methods 的键一致
- 的 on_* 方法签名是 `on_x(callback)`，callback 接收 payload 字典
- 校验：`obox.ui.component_protocol.validate_component_class(tag, cls)`
- 事件名取 `obox/api/events.py` 的常量，其中 `CLOSE = "close"` 供浮层关闭事件使用

## card：可选中的容器

| 项 | 契约 |
|---|---|
| 状态 | 无（`supported_states = ()`）；选中态不进状态机，由 Choice 或宿主调用 `set_selected(bool)` |
| 事件 | `click` -> `on_click`，payload `{"value": <value 属性，缺省取组件 id>}` |
| 容器 | `container_layout()` 返回 QVBoxLayout（边距 16/14/16/16、间距 6），子组件纵向排布 |
| 选中外观 | **不画对勾**：选中只把底色换成 `ACCENT_SOFT`、描边换成 1px `ACCENT`；未选中底色 `CARD_SURFACE`、描边 `CARD_BORDER`；悬停描边同样转 `ACCENT`；圆角 `RADIUS_CARD` |

## modal：浮层容器

容器组件：panel 里放任意子组件，直接子级的 Button 进底部按钮区。

| 项 | 契约 |
|---|---|
| 状态 | `visible`（`is_visible` / `set_visible`）、`text`（`text` / `set_text`，只影响旧写法生成的正文标签） |
| 事件 | `close` -> `on_close`，payload `{"reason": "button" 或 "esc" 或 "overlay", "value": 按钮文本或 ""}` |
| 容器 | `container_layout()` 返回装配槽 `ModalSlot`：**直接子级的 Button 进底部按钮区**（右对齐、间距 8），其余子组件进正文滚动区 |
| 属性 | `title`（缺省「提示」）、`text`（旧写法正文）、`width` / `height`（面板初值）、`variant`、`close_on_esc`、`close_on_overlay` |
| 尺寸 | 下限 320x160，上限宿主窗口的 90%；`width` 缺省 420，`height` 不给按内容自适应（仍受上下限约束）；宿主窗口改尺寸时覆盖层同步重设几何 |
| 拖拽缩放 | 面板右下角 16x16 热区可拖，对角线光标，拖动同样按 320x160 与宿主 90% 夹取 |
| 关闭语义 | 点任意底部按钮即关闭（reason=button，value 是按钮文本）；`close_on_esc` 缺省 true，Esc 关闭（reason=esc）；`close_on_overlay` 缺省 false，显式开才在点面板外关闭（reason=overlay）；关闭只隐藏覆盖层（`visible` 随之变假），组件不销毁 |
| variant | `info`（缺省）/ `confirm` / `danger`，只差左侧徽标图标（i / i / !）与主按钮色：confirm 把最后一个底部按钮染 primary，danger 染 danger，info 不染；非法值抛 ValueError |
| 旧写法 | 只写 `title` / `text`、没有子组件和按钮时，渲染「标题 + 正文 + 知道了」，按钮同样发 reason=button、value=「知道了」 |

## button：外观变体

| 项 | 契约 |
|---|---|
| 状态 | `text`、`visible`、`enabled` |
| 事件 | `click` -> `on_click`、`contextmenu` -> `on_contextmenu`，payload 均为 `{}` |
| 外观 | `type` 取 primary / secondary / ghost / danger，缺省 secondary |
| 运行时染色 | `ButtonWidget.set_variant(variant)`（两套主题都有）：就地改外观并重绘，非法值退回 secondary；浮层用它把主按钮染成 primary / danger |

## provider 契约

kit 的 provider 至少提供：name、version、mode、stylesheet、palette；另有 spacing、icon_muted/icon_active、font_dir、title_muted/title_active、danger 供宿主使用。组件类不再由主题提供，宿主用 obox/ui/components 的 COMPONENT_TYPES。

## 容器组件

Card、Div、Choice、Tabs、Modal 实现 `container_layout()`，子组件由装配器放进去；Flex 用自定义 QLayout 排布。Card/Div 纵向、Tabs 进内容区、Choice 复用 Card 的选中逻辑，Modal 的装配槽把直接子级的 Button 分流到底部按钮区。
## collapse

折叠面板：`title` 标题、`open` 初始展开；状态 open/title/visible，事件 toggle。组件实现由 obox 提供，主题只出样式。
