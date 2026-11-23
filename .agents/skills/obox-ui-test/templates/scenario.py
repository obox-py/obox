"""自定义 verify 场景骨架（贴进 scripts/verify_ui.py 的 main 流程）。

作为函数给出参数，避免模板文件出现未定义名字；复制到 verify_ui.py 后去掉参数即可。
"""

from __future__ import annotations


def scenario(driver, obox, check) -> None:
    # 1. 等待目标就绪（不要 sleep 固定时长）
    ready = driver.wait_until(lambda: "demo.main" in obox.window.view_ids(), timeout=10)
    check("视图已挂载", ready, str(obox.window.view_ids()))

    # 2. 与组件交互
    button = obox.registry.lookup("demo.obox", "demo-btn")
    driver.click(button.widget)

    # 3. 断言状态
    status = obox.registry.lookup("demo.obox", "demo-status")
    getter = status.state_accessors["text"][0]
    changed = driver.wait_until(lambda: getattr(status, getter)() == "按钮被点击了", timeout=10)
    check("点击事件往返", changed, str(getattr(status, getter)()))

    # 4. 截图留证
    driver.screenshot(obox.window, f"{obox.theme_name}_99_custom")
