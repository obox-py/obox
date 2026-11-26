"""表格：QTableWidget + 主题 QSS。"""

from __future__ import annotations

from typing import Any

from obox.qt import QAbstractItemView, QTableWidget, QTableWidgetItem

from .. import palette
from .base import Component, border_css


class TableComponent(Component):
    tag = "table"
    supported_states = ("value", "visible", "enabled")
    state_accessors = {
        "value": ("value", "set_value"),
        "visible": ("is_visible", "set_visible"),
        "enabled": ("is_enabled", "set_enabled"),
    }
    supported_events = ("click",)
    event_methods = {"click": "on_click"}

    def build_widget(self, attrs: dict[str, str]) -> QTableWidget:
        widget = QTableWidget()
        columns = [item.strip() for item in attrs.get("columns", "").split(",") if item.strip()]
        widget.setColumnCount(len(columns))
        widget.setHorizontalHeaderLabels(columns)
        widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        widget.verticalHeader().setVisible(False)
        widget.setFixedHeight(int(attrs.get("height", "180")))
        widget.setStyleSheet(border_css(attrs, "none", palette.LINE))
        return widget

    def value(self) -> list[list[str]]:
        rows = []
        for row in range(self.widget.rowCount()):
            rows.append(
                [
                    self.widget.item(row, column).text() if self.widget.item(row, column) else ""
                    for column in range(self.widget.columnCount())
                ]
            )
        return rows

    def set_value(self, value: Any) -> None:
        rows = value or []
        self.widget.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for column_index, cell in enumerate(row):
                if column_index >= self.widget.columnCount():
                    break
                self.widget.setItem(row_index, column_index, QTableWidgetItem(str(cell)))

    def on_click(self, callback) -> None:
        self.widget.cellClicked.connect(lambda row, column: callback({"row": row, "column": column}))
