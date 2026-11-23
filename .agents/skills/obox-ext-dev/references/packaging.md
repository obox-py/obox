# 打包与安装

```bash
uv run python scripts/pack_extension.py extensions/demo
# 产物：dist/demo.obox.0.1.0.oix
```

zip 根目录包含：

- `extension.pyd`（入口编译产物）
- `extension.json`
- `i18n.json`（若有）
- `assets/`
- `views/`（若有）

安装：把 .oix 放进 `.obox/extensions`，启动时解压到 `.obox/extensions/{name}.{publisher}` 并加载；加载顺序先安装目录、后 extensions/。

注意：打包用 Nuitka 逐文件编译；扩展目录内的模块名要全局唯一，避免同名冲突。
## 安装后的扩展位置

安装版有三个扩展根，优先级 用户安装 > 系统 > 源码：

1. `%LOCALAPPDATA%\\obox\\extensions`：用户安装的 .oix 解压目录
2. `<安装目录>\\extensions`：随装的系统扩展（app、settings），已解压
3. `extensions/`：源码开发目录（仅源码运行）

安装目录布局：obox.exe 与运行时、.theme/{light,dark}、extensions/{app,settings}；数据目录在 LOCALAPPDATA。
