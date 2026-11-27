# 命名空间 API（window / workspace / network 等）

所有 API 第一个参数是 `ctx`（OboxContext），函数名与参数 camelCase，语义对齐 VS Code。完整清单见项目 docs/api.md。

## 常用

```python
from obox.api import window, workspace, commands, storage, network, message, log

window.showInformationMessage(ctx, "完成", "打开")
window.showMessageBox(ctx, {"type": "warning", "message": "继续？", "buttons": ["继续", "取消"]})
window.createWindow(ctx, {"title": "详情", "oml": "views/detail.oml", "modal": True})
commands.executeCommand(ctx, "demo.refresh")
storage.globalState.update(ctx, "count", 1)
network.request(ctx, {"url": "https://example.com", "noProxy": True})
log.createOutputChannel(ctx, "demo").info("started")
```

## ctx 绑定写法

```python
ctx.window.showInformationMessage("完成")
ctx.storage.globalState.update("count", 1)
```

ctx.window 等命名空间已绑定 ctx，调用时不用再传；需要显式时用 window.showInformationMessage(ctx, ...)。

## 规则

- ctx 只读；订阅放 `ctx.subscriptions.add(...)`
- window 类用 ctx.windowId 定父窗口；空为主窗口
- 网络代理只由设置页决定，调用只传 `noProxy`
- 不直接 import PySide6/PyQt5；确需 Qt 用 `obox.qt`