"""测试公共设置：无窗口环境下用 offscreen 平台。"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
