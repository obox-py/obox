# oml 视图语法

oml 与内联片段同一套语法，注册时给相对扩展目录的路径。

## 标签（21）

div、text、button、input、textarea、checkbox、radio、switch、select、slider、tag、table、tabs、modal、notification、flex、card、choice、alert、image、navitem、chart、collapse

`Modal` 是容器：正文放任意子组件，直接子级的 `<Button>` 进底部按钮区（点任一底部按钮即关闭），写法见后面「容器」。

## 指令与绑定

```html
<Card id="app-card-{{app.id}}" value="{{app.id}}" o-for="app in apps" on_click="true">
  <Text id="app-name-{{app.id}}" text="{{app.title}}" />
</Card>
<Text id="empty" o-if="!apps.length" text="没有数据" />
```

- `o-for="item in items"`：作用域内可用 item 与 index，可嵌套
- `o-if="expr"`：假值不渲染
- 绑定 `{{expr}}`：点路径、`.length`、字面量、`== != > < !`；i18n 引用会先被替换
- 数据来自 `register_view(..., data={...})` 或宿主注入/更新，更新时只重建指令区域

## 事件

组件支持的 `on_*`：button click/contextmenu；input input/change/focus/blur；checkbox checkedchange/click；radio/switch checkedchange；select/slider/tabs change；card click；modal close；navitem click；table click。

`Modal` 的 `on_close` 载荷是 `{"reason": "button" | "esc" | "overlay", "value": 按钮文本或 ""}`：点底部按钮、Esc、点遮罩（需 `close_on_overlay="true"`）都会发；旧写法只写 title/text 时自动补的「知道了」按钮同样走 reason=button。

## 容器

Card、Div、Choice、Tabs、Modal 是容器：Card/Div/Modal 的子组件纵向排布；Choice/Flex 用 Flex 规则排布（横向、可换行）。

`Modal` 多一层分流：直接子级的 `Button` 进底部按钮区（右对齐），其余子组件进正文滚动区；`title`、`width`/`height`、`variant`、`close_on_esc`、`close_on_overlay` 由属性给。

```html
<Modal id="confirm" title="确认" variant="confirm" width="460" on_close="true">
  <Text id="confirm-text" text="确定要删除吗？" />
  <Button id="confirm-cancel" text="取消" />
  <Button id="confirm-ok" text="确定" />
</Modal>
```

## chart（图表）

chart 由 obox 提供（不在主题里），用 matplotlib 的 QtAgg 画布渲染，可交互：滚轮缩放、拖动平移、悬停显示坐标、右下角重置。

```html
<Chart id="g-chart" data='{"type":"line","series":[{"name":"甲","points":[{"x":0,"y":1},{"x":1,"y":3}]}],"x":["一","二"]}' title="趋势" />
```

- data 是 JSON：type 取 line、bar、scatter；series 每项 {name, points:[{x,y}]}；x 可选标签数组
- 组件自带 matplotlib 导航工具栏（Home/前进/后退/平移/缩放/子图/保存），状态：data、title、code；data 走 JSON 结构，code 是 matplotlib Python 代码（可用 fig/ax/plt/np），二者有 code 时优先
- 示例见 extensions/chartdemo：扩展发 COMPONENT_MODIFY_MSG(state_type=code) 即可换成图表代码
- 数据从扩展进程经消息下发，宿主进程不需要 matplotlib

## collapse（折叠面板）

```html
<Collapse id="group-account" title="账号" open="true">
  <Input id="u" value="{{form.username}}" />
</Collapse>
```

- 标题可点，展开/收起正文；子组件写在面板里，装配进入正文布局
- 状态：open（bool）、title、visible；事件：toggle（回调收到 {open}）

## 选择文件与目录（picker）

```python
from obox.api.picker import picker_open_message

request = context.request(
    picker_open_message(
        context.extension_id,
        mode="file",              # file 或 dir
        extensions=["txt", "md"],  # 只对文件生效
        multi=True,
        title="选择文件",
        start_path="",            # 空则从用户主目录开始
        window_id="",             # App 窗口传入 window_id，只阻塞该窗口
        ssh=None,                 # 或 {"host","port","user","password","key_path","passphrase"}
    ),
    timeout=3600,                 # 选择器可能停留很久，不要用默认 5 秒
)
payload = request.result(60)  # 远端指纹/输入可能很久，发起时给足 timeout
# {"paths": [...], "cancelled": false, "error": "..."}；远端路径为 {"path","host","user"}
```

- 对话框对发起窗口模态：主窗口发起阻塞主窗口，App 窗口发起只阻塞该窗口
- 远端浏览使用 paramiko，主机指纹自动记录，不弹确认；凭据只存在于本次请求
- 列表首行「..」返回上级；隐藏文件默认显示；远端左侧只列服务器入口
- 选择器可能停留很久，发起请求要显式给长 timeout（示例用 3600 秒）