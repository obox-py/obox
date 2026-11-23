# 构建与切换

```bash
uv run python scripts/build_theme.py            # 两套
uv run python scripts/build_theme.py light      # 单套
```

- 源码在 `theme/{light,dark}`，产物在 `.theme/{name}/{name}.pyd` + `theme.json` + `fonts/`
- 构建前要关闭正在运行的 obox（Windows 会锁 pyd）
- 启动：`uv run obox`，或 `--theme dark`，或改 `.obox/config.json` 的 theme
- 运行中切换：设置页「外观」或 `OboxApp.switch_theme(name)`，失败保留当前套件
- 字体：套件自带 fonts 目录，启动时注册；改字体只影响 pyd 之外的资源，但 family 名在 QSS 里，改名要重编
