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
    from .app import run

    return run(
        extensions_dir=args.extensions_dir,
        exit_after=args.exit_after,
        theme=args.theme,
        language=args.lang,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
