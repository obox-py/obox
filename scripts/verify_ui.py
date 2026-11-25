"""启动 obox，用鼠标与键盘驱动示范扩展，产出截图与日志。"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui_driver import PROJECT_ROOT, UiDriver, setup_logging  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="obox 界面验证")
    parser.add_argument("--show", action="store_true", help="使用真实窗口而不是 offscreen")
    parser.add_argument("--theme", default="", help="指定主题套件，例如 light 或 dark")
    args = parser.parse_args(argv)
    if not args.show:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

    from PySide6.QtWidgets import QApplication

    from obox.app import OboxApp

    logger = setup_logging("verify")
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("obox")
    obox = OboxApp(PROJECT_ROOT, theme=args.theme, language="zh-CN")
    driver = UiDriver(logger)
    obox.start()
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        logger.info("%s %s %s", "PASS" if ok else "FAIL", name, detail)
        if not ok:
            failures.append(name)

    try:
        ready = driver.wait_until(lambda: "demo.main" in obox.window.view_ids(), timeout=30)
        check("扩展视图已挂载", ready, str(obox.window.view_ids()))
        check("启动落在应用页", obox.window.current_view_id() == "app.main", obox.window.current_view_id())
        if obox._tray is not None:
            menus = [action.text() for action in obox._tray.menu().actions()]
            grouped = (
                menus[0] == "打开 obox 窗口"
                and "刷新扩展" in menus
                and "打开扩展目录" in menus
                and menus[-2:] == ["设置", "退出"]
            )
            check("托盘菜单三组结构", grouped, str(menus))
        buttons = obox.window.rail_buttons()
        check("侧栏出现扩展图标", len(buttons) >= 1, f"按钮数={len(buttons)}")

        demo_buttons = [button for button in buttons if button.toolTip() == "示范"]
        if demo_buttons:
            driver.click(demo_buttons[0])
            switched = driver.wait_until(
                lambda: obox.window._stack.currentWidget() is obox.window._views["demo.main"], timeout=5
            )
            check("点击侧栏切换到扩展视图", switched, str(obox.window.view_ids()))
        driver.screenshot(obox.window, f"{obox.theme_name}_01_launch")

        status = obox.registry.lookup("demo.obox", "demo-status")
        text_of = getattr(status, status.state_accessors["text"][0])
        check("初始文本", text_of() == "等待点击", str(text_of()))
        title = obox.registry.lookup("demo.obox", "demo-title").text()
        check("i18n 文案已替换", title == "obox 示范扩展", title)
        button = obox.registry.lookup("demo.obox", "demo-btn")
        driver.click(button.widget)
        changed = driver.wait_until(lambda: text_of() == "按钮被点击了", timeout=10, interval=0.005)
        check("点击事件往返", changed, str(text_of()))
        driver.screenshot(obox.window, f"{obox.theme_name}_02_click")

        field = obox.registry.lookup("demo.obox", "demo-input")
        value_of = getattr(field, field.state_accessors["value"][0])
        driver.type_text(field.widget, "obox")
        typed = driver.wait_until(lambda: value_of() == "obox", timeout=5)
        check("键盘输入生效", typed, str(value_of()))
        driver.screenshot(obox.window, f"{obox.theme_name}_03_typing")

        obox.supervisor.invoke_command("demo.hello")
        from_command = driver.wait_until(lambda: text_of() == "来自命令", timeout=10)
        check("命令往返并回改状态", from_command, str(text_of()))
        check("底部栏已显示", obox.window._bottom.isVisible(), "bottom 容器")

        gallery_ids = [view for view in obox.window.view_ids() if view.startswith("gallery.")]
        check("画廊扩展已挂载", bool(gallery_ids), str(gallery_ids))
        if gallery_ids:
            rail = {button.toolTip(): button for button in obox.window.rail_buttons()}
            if "组件" in rail:
                driver.click(rail["组件"])
                driver.wait_until(
                    lambda: obox.window._stack.currentWidget() is obox.window._views[gallery_ids[0]],
                    timeout=5,
                )
                driver.screenshot(obox.window, f"{obox.theme_name}_05_gallery")
                from PySide6.QtWidgets import QScrollArea

                view = obox.window._views[gallery_ids[0]]
                scrolls = [view] if isinstance(view, QScrollArea) else view.findChildren(QScrollArea)
                if scrolls:
                    bar = scrolls[0].verticalScrollBar()
                    bar.setValue(int(bar.maximum() * 0.55))
                    driver.screenshot(obox.window, f"{obox.theme_name}_06_gallery_cards")
                    card_a = obox.registry.lookup("gallery.obox", "g-card-a")
                    card_b = obox.registry.lookup("gallery.obox", "g-card-b")
                    driver.click(card_a.widget)
                    driver.click(card_b.widget)
                    choice = obox.registry.lookup("gallery.obox", "g-choice")
                    picked = choice.value()
                    check("多选选中两张卡片", len(picked) == 2, str(picked))
                    driver.screenshot(obox.window, f"{obox.theme_name}_07_choice_selected")
                    top_alert = obox.registry.lookup("gallery.obox", "g-alert-info")
                    top_alert.set_visible(True)
                    check("顶部提醒可见", top_alert.is_visible(), "g-alert-info")
                    driver.screenshot(obox.window, f"{obox.theme_name}_08_alert_top")
                    top_alert.set_visible(False)
                    bottom_alert = obox.registry.lookup("gallery.obox", "g-alert-error")
                    bottom_alert.set_visible(True)
                    check("底部提醒可见", bottom_alert.is_visible(), "g-alert-error")
                    driver.screenshot(obox.window, f"{obox.theme_name}_09_alert_bottom")
                    bottom_alert.set_visible(False)
                    free_card = obox.registry.lookup("gallery.obox", "g-card-free")
                    scrolls[0].ensureWidgetVisible(free_card.widget, 60, 60)
                    driver.click(free_card.widget)
                    check("独立卡片可见", free_card.widget.isVisible(), "g-card-free")
                    driver.screenshot(obox.window, f"{obox.theme_name}_10_card")
        modal = obox.registry.lookup("gallery.obox", "g-modal")
        open_modal = obox.registry.lookup("gallery.obox", "g-modal-open")
        if modal is not None and open_modal is not None:
            from PySide6.QtCore import Qt
            from PySide6.QtTest import QTest

            driver.click(open_modal.widget)
            shown = driver.wait_until(lambda: modal.is_visible(), timeout=5)
            check("浮层可由按钮打开", shown, "g-modal")
            driver.screenshot(obox.window, f"{obox.theme_name}_17_modal")
            QTest.keyClick(modal.widget, Qt.Key.Key_Escape)
            esc_closed = driver.wait_until(lambda: not modal.is_visible(), timeout=5)
            check("Esc 关闭浮层", esc_closed, "g-modal")
            driver.click(open_modal.widget)
            driver.wait_until(lambda: modal.is_visible(), timeout=5)
            save_button = obox.registry.lookup("gallery.obox", "g-modal-ok")
            driver.click(save_button.widget)
            button_closed = driver.wait_until(lambda: not modal.is_visible(), timeout=5)
            check("底部按钮关闭浮层", button_closed, "g-modal")

            demo_rail = {button.toolTip(): button for button in obox.window.rail_buttons()}
            legacy = obox.registry.lookup("demo.obox", "demo-modal")
            legacy_button = obox.registry.lookup("demo.obox", "demo-modal-btn")
            if "示范" in demo_rail:
                driver.click(demo_rail["示范"])
                driver.wait_until(
                    lambda: obox.window._stack.currentWidget() is obox.window._views["demo.main"],
                    timeout=5,
                )
                driver.click(legacy_button.widget)
                legacy_shown = driver.wait_until(lambda: legacy.is_visible(), timeout=5)
                check("旧写法浮层仍可打开", legacy_shown, "demo-modal")
                driver.screenshot(obox.window, f"{obox.theme_name}_18_modal_legacy")
                QTest.keyClick(legacy.widget, Qt.Key.Key_Escape)
                driver.wait_until(lambda: not legacy.is_visible(), timeout=5)

        apps_buttons = [button for button in obox.window.rail_buttons() if button.toolTip() == "应用"]
        check("侧栏出现应用入口", bool(apps_buttons), str([b.toolTip() for b in obox.window.rail_buttons()]))
        if apps_buttons:
            driver.click(apps_buttons[0])

            def _card():
                try:
                    return obox.registry.lookup("app.obox", "app-card-demo.notes")
                except Exception:
                    return None

            card_ready = driver.wait_until(lambda: _card() is not None, timeout=10)
            check("应用网格由 o-for 渲染", card_ready, str(_card()))
            driver.screenshot(obox.window, f"{obox.theme_name}_12_apps")
            search = obox.registry.lookup("app.obox", "app-search")

            def _card_present() -> bool:
                try:
                    obox.registry.lookup("app.obox", "app-card-demo.notes")
                    return True
                except Exception:
                    return False

            driver.type_text(search.widget, "zzz")
            filtered = driver.wait_until(lambda: not _card_present(), timeout=5)
            check("无匹配时卡片被过滤", filtered, str(_card_present()))
            from PySide6.QtCore import Qt
            from PySide6.QtTest import QTest

            QTest.keyClick(search.widget, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
            QTest.keyClick(search.widget, Qt.Key.Key_Backspace)
            restored = driver.wait_until(_card_present, timeout=5)
            check("清空搜索恢复全部", restored, str(_card_present()))
            driver.screenshot(obox.window, f"{obox.theme_name}_14_search")
            if card_ready:
                driver.click(_card().widget)

                def _window():
                    return next((w for w in obox._app_windows.values() if w.has_content()), None)

                opened = driver.wait_until(lambda: _window() is not None, timeout=10)
                check("点击卡片打开应用窗口", opened, str(list(obox._app_windows)))
                if opened:
                    title = obox.registry.lookup("demo.obox", "note-title").text()
                    check("应用窗口渲染扩展 UI", title == "示范笔记", title)
                    driver.screenshot(_window(), f"{obox.theme_name}_13_app_window")
                for window in list(obox._app_windows.values()):
                    window.force_close()
                obox._app_windows.clear()

        settings_buttons = [button for button in obox.window.rail_buttons() if button.toolTip() == "设置"]
        check("侧栏出现设置入口", bool(settings_buttons), str([b.toolTip() for b in obox.window.rail_buttons()]))
        if settings_buttons:
            driver.click(settings_buttons[0])

            def _group(group_id: str):
                try:
                    return obox.registry.lookup("settings.obox", f"group-{group_id}")
                except Exception:
                    return None

            settings_ready = driver.wait_until(lambda: _group("appearance") is not None, timeout=10)
            check("设置页分类已渲染", settings_ready, str(obox.window.view_ids()))
            driver.screenshot(obox.window, f"{obox.theme_name}_15_settings")
            if settings_ready:
                from PySide6.QtCore import Qt
                from PySide6.QtTest import QTest

                search_box = obox.registry.lookup("settings.obox", "settings-search")
                search_box.widget.setText("主题")
                search_box.widget.textEdited.emit("主题")
                filtered = driver.wait_until(lambda: _group("language") is None, timeout=5)
                check("设置搜索过滤分类", filtered, "language 仍在")
                driver.screenshot(obox.window, f"{obox.theme_name}_16_settings_search")
                QTest.keyClick(search_box.widget, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
                QTest.keyClick(search_box.widget, Qt.Key.Key_Backspace)
                restored = driver.wait_until(lambda: _group("language") is not None, timeout=5)
                check("清空设置搜索恢复", restored, "language 未恢复")
                about_groups = {group["id"]: group for group in obox._settings_groups()}
                version_item = about_groups["about"]["items"][0]
                check("版本项是只读 label", version_item["type"] == "label", version_item["type"])
                about = _group("about")

                def _version_label():
                    try:
                        return obox.registry.lookup("settings.obox", "item-label-obox.version")
                    except Exception:
                        return None

                if about is not None:
                    driver.click(about.widget)
                    driver.wait_until(lambda: _version_label() is not None, timeout=5)
                    label = _version_label()
                    check("版本号渲染为文本", label is not None, str(label))
                    if label is not None:
                        check("版本号内容非空", bool(label.text()), label.text())
                    driver.screenshot(obox.window, f"{obox.theme_name}_19_about")
                    appearance = _group("appearance")
                    if appearance is not None:
                        driver.click(appearance.widget)

        from types import SimpleNamespace
        from PySide6.QtCore import Qt as _Qt
        from PySide6.QtTest import QTest as _QTest
        from PySide6.QtWidgets import QPushButton

        ext_ready = driver.wait_until(lambda: "extensions.main" in obox.window.view_ids(), timeout=10)
        check("扩展管理已挂载", ext_ready, str(obox.window.view_ids()))
        rail = {button.toolTip(): button for button in obox.window.rail_buttons()}
        check("侧栏出现扩展管理入口", "扩展" in rail, str(list(rail)))
        if "扩展" in rail:
            driver.click(rail["扩展"])
            opened = driver.wait_until(
                lambda: obox.window.current_view_id() == "extensions.main", timeout=5
            )
            check("扩展管理页可打开", opened, obox.window.current_view_id())
            check("扩展列表已下发", len(obox._extensions) >= 3, str(len(obox._extensions)))
            driver.screenshot(obox.window, f"{obox.theme_name}_20_extensions")
            def _card_count() -> int:
                owner = obox.registry._by_owner.get("extensions.obox") or {}
                return len([key for key in owner if key.startswith("ext-card-")])

            before_cards = _card_count()
            search = obox.registry.lookup("extensions.obox", "ext-search")
            search.widget.setText("设置")
            search.widget.textEdited.emit("设置")
            _QTest.qWait(150)
            filtered_cards = _card_count()
            check(
                "扩展搜索过滤卡片",
                0 < filtered_cards < before_cards,
                f"{before_cards} -> {filtered_cards}",
            )
            _QTest.keyClick(search.widget, _Qt.Key.Key_A, _Qt.KeyboardModifier.ControlModifier)
            _QTest.keyClick(search.widget, _Qt.Key.Key_Backspace)
            _QTest.qWait(150)
            check("清空搜索恢复卡片", _card_count() == before_cards, str(_card_count()))

        check("滑块轨道样式存在", "QSlider::groove" in obox.provider.stylesheet, "QSlider::groove")
        theme_before = obox.theme_name
        other_theme = "dark" if theme_before == "light" else "light"
        view_before = obox.window.current_view_id()
        if obox.switch_theme(other_theme):
            check(
                "切主题后仍在原视图",
                obox.window.current_view_id() == view_before,
                f"{view_before} -> {obox.window.current_view_id()}",
            )
            check("切主题生效", obox.theme_name == other_theme, obox.theme_name)
            obox.switch_theme(theme_before)
            check("切回原主题", obox.theme_name == theme_before, obox.theme_name)

        check(
            "标题栏没有语言按钮",
            obox.window._title_bar.findChild(QPushButton, "obox-lang") is None,
            "obox-lang",
        )
        language_items = {
            item["key"]: item
            for group in obox._settings_groups()
            if group["id"] == "language"
            for item in group["items"]
        }
        check("设置页有界面语言项", "obox.language" in language_items, str(language_items))

        hk_label = obox.language_label("zh-HK")
        check("语言项显示原生名", hk_label == "中国香港", hk_label)
        obox._on_settings_set(
            SimpleNamespace(payload={"key": "obox.language", "value": hk_label}, correlation_id="")
        )
        check("切到 zh-HK", obox.i18n.language == "zh-HK", obox.i18n.language)
        fallback_title = driver.wait_until(
            lambda: obox.registry.lookup("demo.obox", "demo-title").text() == "obox 示范扩展",
            timeout=6,
        )
        check("zh-HK 回退 zh-CN", fallback_title, obox.i18n.language)
        obox._on_settings_set(
            SimpleNamespace(payload={"key": "obox.language", "value": "zh-CN"}, correlation_id="")
        )
        view_before_language = obox.window.current_view_id()
        obox._on_settings_set(
            SimpleNamespace(payload={"key": "obox.language", "value": "en-US"}, correlation_id="")
        )
        if obox.i18n.language == "en-US":
            driver.wait_until(
                lambda: obox.registry.lookup("demo.obox", "demo-title").text() == "obox demo extension",
                timeout=5,
            )
            english = obox.registry.lookup("demo.obox", "demo-title").text()
            check("切到英文后视图重建", english == "obox demo extension", english)
            check(
                "切语言后仍在原视图",
                obox.window.current_view_id() == view_before_language,
                f"{view_before_language} -> {obox.window.current_view_id()}",
            )
            driver.screenshot(obox.window, f"{obox.theme_name}_11_lang_en")
            obox._on_settings_set(
                SimpleNamespace(payload={"key": "obox.language", "value": "zh-CN"}, correlation_id="")
            )
            check("从设置页切回中文", obox.i18n.language == "zh-CN", obox.i18n.language)
        app_ids = {app["id"] for app in obox._apps}
        check("远程桌面应用已注册", "rdp.app" in app_ids, str(sorted(app_ids)))
        check("网页应用已注册", "webapp.app" in app_ids, str(sorted(app_ids)))

        def _owner_component(owner: str, component_id: str):
            try:
                return obox.registry.lookup(owner, component_id)
            except Exception:
                return None

        if "rdp.app" in app_ids:
            obox._open_app("rdp.app")
            rdp_ready = driver.wait_until(
                lambda: _owner_component("rdp.chenzhi", "rdp-root") is not None, timeout=8
            )
            check("远程桌面页已渲染", rdp_ready, "")
            rdp_window = obox._app_windows.get("rdp.app")
            if rdp_window is not None:
                driver.screenshot(rdp_window, f"{obox.theme_name}_22_rdp")
        def _click(owner: str, component_id: str) -> None:
            from obox.api.message import Message

            obox.bus.send(
                Message(
                    src="obox",
                    dst=owner,
                    msg_id="COMPONENT_EVENT_MSG",
                    payload={"id": component_id, "event": "click", "value": ""},
                )
            )

        if "rdp.app" in app_ids:
            _click("rdp.chenzhi", "rdp-new")
            modal_open = driver.wait_until(
                lambda: getattr(_owner_component("rdp.chenzhi", "conn-modal"), "is_visible", lambda: False)(),
                timeout=5,
            )
            check("远程桌面新建走模态框", modal_open, "")
            rdp_window = obox._app_windows.get("rdp.app")
            if rdp_window is not None:
                driver.screenshot(rdp_window, f"{obox.theme_name}_24_rdp_modal")

        if "webapp.app" in app_ids:
            obox._open_app("webapp.app")
            web_ready = driver.wait_until(
                lambda: _owner_component("webapp.chenzhi", "webapp-root") is not None, timeout=8
            )
            check("网页应用页已渲染", web_ready, "")
            web_window = obox._app_windows.get("webapp.app")
            if web_window is not None:
                driver.screenshot(web_window, f"{obox.theme_name}_23_webapp")
            _click("webapp.chenzhi", "webapp-new")
            web_modal = driver.wait_until(
                lambda: getattr(_owner_component("webapp.chenzhi", "site-modal"), "is_visible", lambda: False)(),
                timeout=5,
            )
            check("网页应用新建走模态框", web_modal, "")
            if web_window is not None:
                driver.screenshot(web_window, f"{obox.theme_name}_25_webapp_modal")

        if "chartdemo.main" in obox.window.view_ids():
            obox.window.show_view("chartdemo.main")
            from obox.api.message import Message as _Msg

            obox.bus.send(
                _Msg(
                    src="obox",
                    dst="chartdemo.obox",
                    msg_id="COMPONENT_EVENT_MSG",
                    payload={"id": "demo-line", "event": "click", "value": ""},
                )
            )

            def _chart_ready() -> bool:
                try:
                    chart = obox.registry.lookup("chartdemo.obox", "demo-chart")
                    return bool(chart._figure and chart._figure.axes and len(chart._figure.axes[0].lines) >= 2)
                except Exception:
                    return False

            chart_ok = driver.wait_until(_chart_ready, timeout=8)
            check("matplotlib 示例渲染折线", chart_ok, "")
            driver.screenshot(obox.window, f"{obox.theme_name}_26_matplotlib")

        driver.screenshot(obox.window, f"{obox.theme_name}_04_final")
    finally:
        obox.supervisor.stop()
        obox.window.allow_close()
        obox.window.close()
        obox.window.deleteLater()
        QApplication.processEvents()

    logger.info("结果：%d 项失败", len(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())