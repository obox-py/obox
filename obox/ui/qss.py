"""扩展 QSS 的选择器白名单过滤。"""

from __future__ import annotations

import re

_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")


def _selector_allowed(selector: str, allowed_ids: set[str]) -> bool:
    head = selector.strip().split()[0] if selector.strip() else ""
    if not head.startswith("#"):
        return False
    target = head[1:].split(":")[0].split(".")[0]
    return target in allowed_ids


def filter_stylesheet(source: str, allowed_ids: set[str]) -> tuple[str, list[str]]:
    """保留只作用于本扩展组件的规则，返回（可用样式，被拒选择器列表）。"""
    kept: list[str] = []
    rejected: list[str] = []
    for selectors, body in _RULE.findall(source):
        group = [item.strip() for item in selectors.split(",") if item.strip()]
        if not group:
            continue
        if all(_selector_allowed(selector, allowed_ids) for selector in group):
            kept.append(f"{','.join(group)} {{{body}}}")
        else:
            rejected.extend(selector for selector in group if not _selector_allowed(selector, allowed_ids))
    return "\n".join(kept), rejected
