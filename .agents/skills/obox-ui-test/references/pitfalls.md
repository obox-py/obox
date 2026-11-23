# 常见坑

- **中文输入**：QTest.keyClicks 打不出中文，会看起来像卡死；用 `widget.setText(text); widget.textEdited.emit(text)`
- **配置污染**：切语言/主题会写 `.obox/config.json`，后续测试读到英文/深色；验证脚本传 `language="zh-CN"`，必要时复位配置
- **pyd 过期**：改过 theme/ 或组件后不重编，界面还是旧实现；先 build_theme.py
- **窗口截图**：`grabWindow(hwnd)` 可能抓到整屏；用 GetWindowRect + `grabWindow(0, x, y, w, h)`
- **应用窗口断言**：窗口在 `obox._app_windows` 里，内容组件仍注册在扩展名下
- **滚动**：截图前用 `scroll.ensureWidgetVisible(widget)`，不要直接滚到底
