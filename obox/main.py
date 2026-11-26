"""obox 入口：python -m obox.main。"""

from __future__ import annotations

import argparse
import sys

from . import __version__


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="obox", description="obox 桌面工作台")
    parser.add_argument("--version", action="store_true", help="打印版本后退出")
    parser.add_argument("--extensions-dir", default="", help="覆盖扩展目录")
    parser.add_argument("--theme", default="", help="覆盖主题套件（默认读配置，缺省 light）")
    parser.add_argument("--lang", default="", help="覆盖界面语言（BCP-47，缺省 zh-CN）")
    parser.add_argument("--exit-after", type=float, default=0.0, help="运行若干秒后自动退出")
    parser.add_argument("--qt", choices=["pyside6", "pyqt5"], default="", help="选择 Qt 绑定，缺省读 OBOX_QT 或 pyside6")
    parser.add_argument("--dev-extension", action="append", default=[], help="加载开发目录，可重复")
    parser.add_argument("--debug", action="store_true", help="以 debugpy 启动扩展宿主")
    parser.add_argument("--debug-port", type=int, default=5678, help="debugpy 监听端口")
    parser.add_argument("--no-debug-wait", action="store_true", help="不等待调试器连接")
    parser.add_argument("--no-dev-reload", action="store_true", help="关闭开发目录自动重载")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    if "--extension-host" in arguments:
        from .extensions.host import main as host_main

        return host_main([item for item in arguments if item != "--extension-host"])
    args = parse_args(arguments)
    if args.version:
        print(f"obox {__version__}")
        return 0
    if args.qt:
        import os

        os.environ["OBOX_QT"] = args.qt
    from .app import run

    return run(
        extensions_dir=args.extensions_dir,
        exit_after=args.exit_after,
        theme=args.theme,
        language=args.lang,
        dev_extensions=args.dev_extension,
        debug=args.debug,
        debug_port=args.debug_port,
        debug_wait=not args.no_debug_wait,
        dev_reload=not args.no_dev_reload,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))