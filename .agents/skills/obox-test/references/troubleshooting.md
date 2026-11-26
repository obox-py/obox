# 排障

- **配置污染**：测试断言中文却拿到英文，或主题不一致 → 检查 `.obox/config.json` 的 language/theme；测试与 verify 显式传 `language="zh-CN"`
- **e2e 超时**：宿主未起或扩展激活失败 → 看 `[obox] 宿主状态` 与扩展失败列表
- **pyd 锁**：构建报 WinError 5 → 关掉正在运行的 obox
- **视图不挂载**：oml 路径越界/缺失、清单容器写 main、组件标签未注册 → 看 `[obox] 视图 ... 装配失败`
- **宿主重启循环**：扩展 activate 抛异常 → 看宿主 stderr 的 traceback
- **设置页空白**：SETTINGS_LIST 未送达或视图数据注入过早 → 确认挂载后再推送

## 扩展调试端口

- `--debug` 时宿主等 VS Code attach 才激活，日志出现 debugpy 监听即正常
- 端口被占用：换 `--debug-port` 并同步 launch.json
- 5555/5678 都连不上：确认是源码运行（发布版不带 debugpy）
