# 调试扩展

不安装 .oix，直接把开发目录挂到 obox，用 VS Code 断点调试。

## 前提

- obox 从源码运行（`uv sync` 后），debugpy 在 dev 依赖里；发布版不带调试器
- VS Code 安装 Python Debugger 扩展

## 两个启动配置

1. **调试当前扩展（已安装 obox）**：调用 `%LOCALAPPDATA%\Programs\obox\obox.exe`，带 `--dev-extension ${fileDirname} --debug` 启动，再 attach 5678；需要安装版包含 debugpy（1.0.0 起）
2. **调试 obox 和当前扩展**：用源码启动 obox（VS Code 调试主进程），同时 attach 扩展宿主，两个会话一起调试

两个配置都要求当前编辑器打开目标扩展的 extension.py。

## 选择要调试的扩展

- 最省事：在 VS Code 打开目标扩展的 `extension.py`，选「obox: 调试当前扩展（启动 obox + attach）」——它用 `${fileDirname}` 作为开发目录，并自动完成「启动 obox + attach 宿主」
- 想手动选目录：选「obox: 调试选择目录的扩展（启动 obox + attach）」，输入任意含 extension.json 的目录
- 一个 attach 会话调试整个扩展宿主；`--dev-extension` 可重复，断点落在哪个目录就调试哪个扩展
- 注意「obox: 调试当前扩展（启动 obox + attach）」必须在当前编辑器打开 extension.py 时用；打开别的文件会取错目录

## 已安装的扩展现有代码不一样？

安装后的扩展是 `extension.pyd`（编译产物），没有源码与调试信息，不能对安装产物下断点。正确做法是把**同一份源码目录**用 `--dev-extension` 挂进来：宿主按 dev 来源激活，同 id 时会覆盖本次会话里的安装版本，断点落在源码上。调试的是源码，不是安装副本；两者行为差异要先在源码里复现。

## 步骤

1. 启动 obox 并加载开发目录（`--dev-extension` 可重复）：

   ```bash
   uv run obox --dev-extension D:\work\hello --debug
   ```

2. VS Code 里选「obox: 仅 attach 扩展宿主（obox 已运行）」，端口 5678；宿主会等 attach 后再激活扩展。
3. 在开发目录的 `extension.py` 打断点，操作界面触发对应代码。
4. 保存文件会重启宿主并重新激活；调试时加 `--no-dev-reload` 避免断点被打断。

## 参数

| 参数 | 作用 |
|---|---|
| `--dev-extension PATH` | 加载开发目录，可重复；写入配置 dev_extensions |
| `--debug` | 宿主以 debugpy 启动 |
| `--debug-port N` | 监听端口，默认 5678 |
| `--no-debug-wait` | 不等待 attach，立即激活 |
| `--no-dev-reload` | 关闭开发目录自动重载 |

## 扩展自己的仓库

在扩展仓库放 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "attach obox 扩展宿主",
      "type": "debugpy",
      "request": "attach",
      "connect": {"host": "127.0.0.1", "port": 5678},
      "justMyCode": false,
      "pathMappings": [
        {"localRoot": "${workspaceFolder}", "remoteRoot": "${workspaceFolder}"}
      ]
    }
  ]
}
```

## 运行中增删

```python
from obox.api.extensions import DEV_EXTENSION_ADD_MSG, DEV_EXTENSION_REMOVE_MSG
from obox.api.message import Message
bus.send(Message(src="obox", dst="obox", msg_id=DEV_EXTENSION_ADD_MSG, payload={"path": r"D:\work\hello"}))
```

## 常见问题

- `ECONNREFUSED 127.0.0.1:5678`：宿主还没开始监听就 attach 了。用「obox: 调试当前扩展（启动 obox + attach）」，它的 attach 会先等 5678 端口；若已有 obox 在运行，先退出它，否则新实例会被单实例逻辑挡掉


- 端口占用：换 `--debug-port`，同步改 launch.json
- attach 后没停：确认断点在开发目录的源码上，`justMyCode: false`，pathMappings 指向同一路径
- 扩展没出现：`--debug` 默认等 attach，先连调试器再操作界面
- 保存后断点丢失：宿主重启导致，调试期间用 `--no-dev-reload`
- 列表显示 origin=dev：正常，表示来自开发目录；不会写安装目录