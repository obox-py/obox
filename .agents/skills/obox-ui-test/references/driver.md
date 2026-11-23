# UiDriver

源码：`scripts/ui_driver.py`。

| 方法 | 说明 |
|---|---|
| `click(widget)` | 移动到控件中心并点击 |
| `type_text(widget, text)` | 聚焦后逐字符输入（ASCII 可靠；中文用 setText + textEdited.emit） |
| `screenshot(widget, name)` | 抓取控件所在窗口，保存到 tmp/pics/{name}.png |
| `wait_until(predicate, timeout=5, interval=0.02)` | 轮询条件，处理 Qt 事件 |

等待策略：状态变化用 `wait_until`，不要用固定 sleep；消息往返一般 5–10 秒足够。

## 浮层（Modal）怎么驱动

UiDriver 没有浮层专用方法，键盘/遮罩/拖拽直接用 QTest 发事件；浮层挂在宿主窗口上，截图仍传 `obox.window`。

| 动作 | 写法 |
|---|---|
| 打开 | `driver.click(open_button.widget)`，再 `driver.wait_until(lambda: modal.is_visible())` |
| Esc | `QTest.keyClick(modal.widget, Qt.Key.Key_Escape)`：覆盖层打开时已拿焦点 |
| 点遮罩 | `QTest.mouseClick(modal.widget, Qt.MouseButton.LeftButton, pos=QPoint(2, 2))`；默认不关，浮层写了 `close_on_overlay="true"` 才关 |
| 点底部按钮 | 用 registry 取按钮组件，`driver.click(button.widget)`；点任意底部按钮都会关闭 |
| 拖拽缩放 | 对 `modal.widget.findChild(QWidget, "obox-modal-card")` 依次发 QMouseEvent press / move / release，位移按 globalPosition 算 |
| 等关闭 | `driver.wait_until(lambda: not modal.is_visible())`，不要 sleep |

- 关闭后扩展侧收到 `{reason: "button" 或 "esc" 或 "overlay", value: 按钮文本或 ""}`；断言用 `on_close` 回调收集的 payload，或看事件往返后的文本
- 尺寸与拖拽受 320x160 下限、宿主窗口 90% 上限夹取，断言按夹取后的值写
- variant 的主按钮染色只在首次显示时套用一次；按钮改色后用 `button.grab()` 取像素断言更稳，截图前不需要额外等待（screenshot 已内置一帧）
- 旧写法浮层（只写 title/text）会自动补「知道了」按钮，驱动方式与普通底部按钮相同
