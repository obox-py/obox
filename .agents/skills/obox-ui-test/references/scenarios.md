# verify_ui 场景与截图

| 编号 | 场景 | 断言要点 |
|---|---|---|
| 01 | 启动并切到示范视图 | 启动落在 app.main 应用页；扩展视图挂载、侧栏图标出现 |
| 02 | 点击按钮 | 事件往返后文本变化 |
| 03 | 输入框打字 | value 变为输入内容 |
| 04 | 命令与底部栏 | 命令回改状态、bottom 可见 |
| 05 | 画廊首页 | 全部组件渲染 |
| 06 | 画廊卡片区 | 滚动后卡片可见 |
| 07 | 多选卡片 | value 含两项、背景变色 |
| 08 | 顶部提醒 | alert 可见 |
| 09 | 底部提醒 | offset 生效 |
| 10 | 独立卡片 | click 事件回到扩展 |
| 11 | 设置页切英文 | 语言入口只在设置页，标题栏已无语言按钮；视图按新语言重建，且仍停在设置页 |
| 12 | 应用网格 | o-for 渲染、搜索框存在 |
| 14 | 应用搜索 | 无匹配时卡片消失、清空恢复 |
| 13 | 应用窗口 | 点卡片打开扩展提供的窗口 |
| 15 | 设置页 | 分类与设置项渲染 |
| 16 | 设置搜索 | 过滤后只剩匹配分类 |
| 17 | 浮层 | 按钮打开 g-modal、正文与底部按钮就位；Esc 关闭；点底部按钮关闭 |
| 18 | 旧写法浮层 | demo-modal 只写 title/text 仍渲染正文与「知道了」 |
| 19 | 设置关于页 | 版本项是 label，渲染为文本而不是输入框 |
| 23 | 网页应用 | App 卡片打开网页应用，列表/新建表单可用 |
| 25 | 网页应用表单 | 新建/编辑站点走模态框，保存后关闭 |
| 24 | 远程桌面表单 | 新建/编辑连接走模态框，保存后关闭 |
| 22 | 远程桌面 | App 卡片打开远程桌面，列表/新建表单可用 |
| 20 | 扩展管理页 | 侧栏有「扩展」入口，每行一个扩展，搜索能过滤行 |

截图落在 `tmp/pics/{theme}_NN_name.png`。有托盘的环境还会断言托盘菜单的三组结构（打开 obox 窗口 ‖ 切换主题/切换语言/刷新扩展/打开扩展目录 ‖ 设置/退出）。

## 浮层（17、18）

scripts/verify_ui.py 里已自动化的断言：

| 动作 | 断言 | 截图 |
|---|---|---|
| 点 `g-modal-open` | `g-modal` 的 `visible` 为真 | `{theme}_17_modal` |
| `QTest.keyClick(modal.widget, Qt.Key.Key_Escape)` | 浮层关闭 | 无 |
| 再打开后点 `g-modal-ok` | 点底部按钮即关闭 | 无 |
| 切到示范视图点 `demo-modal-btn` | 旧写法 `demo-modal` 打开，渲出正文与「知道了」 | `{theme}_18_modal_legacy` |

同一条浮层契约里、verify_ui 尚未覆盖（改浮层时仍需单测或人工核对）：

| 项 | 预期 |
|---|---|
| 点遮罩默认不关 | `close_on_overlay` 缺省 false，点面板外不发 close |
| 遮罩 opt-in | 写了 `close_on_overlay="true"` 才关，reason=overlay（画廊 `g-modal` 就是这种） |
| 关闭载荷 | `{reason: button/esc/overlay, value: 按钮文本或 ""}` |
| 拖拽缩放 | 面板右下 16x16 热区可拖，范围 320x160 到宿主窗口 90% |
| variant | confirm 把首个底部按钮染 primary、danger 染 danger、info 不染 |
| 尺寸 | width 缺省 420，小于 320 取 320，超过宿主 90% 取 90%；height 缺省按内容 |

定位用的对象名：`obox-modal-overlay`（覆盖层）、`obox-modal-card`（面板）、`obox-modal-title`、`obox-modal-body`；底部按钮区里就是普通 ButtonWidget。

## 语言场景（11）

标题栏的语言按钮已移除，语言入口只在设置页：脚本先断言标题栏没有 `obox-lang` 按钮、设置页有 `obox.language` 项，再直接调 `obox._on_settings_set({"key": "obox.language", "value": "en-US"})`（等价于点该设置项）切英文，断言 `demo-title` 变为 `obox demo extension` 后截图 `{theme}_11_lang_en`，最后切回 zh-CN。