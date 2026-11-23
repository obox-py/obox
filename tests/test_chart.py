"""图表组件：数据渲染、类型切换与交互入口。"""

from __future__ import annotations

import json

import pytest

from obox.ui.components.chart import ChartComponent

pytest.importorskip("matplotlib")


def _chart(data: dict) -> ChartComponent:
    return ChartComponent("c1", "demo.obox", {"data": json.dumps(data)})


def test_renders_line_series(qapp) -> None:
    chart = _chart(
        {
            "type": "line",
            "series": [
                {"name": "甲", "points": [{"x": 0, "y": 1}, {"x": 1, "y": 3}]},
                {"name": "乙", "points": [{"x": 0, "y": 2}, {"x": 1, "y": 1}]},
            ],
        }
    )
    assert chart.widget is not None
    axes = chart._figure.axes
    assert len(axes) == 1
    assert len(axes[0].lines) == 2
    assert axes[0].get_title() == ""


def test_switches_to_bar(qapp) -> None:
    chart = _chart({"type": "bar", "series": [{"name": "甲", "points": [{"x": 0, "y": 2}]}]})
    chart.set_data({"type": "scatter", "series": [{"name": "乙", "points": [{"x": 1, "y": 4}]}]})
    axes = chart._figure.axes[0]
    assert axes.collections
    assert chart.data().startswith('{"type": "scatter"')


def test_title_state(qapp) -> None:
    chart = _chart({"title": "初始"})
    assert chart.title() == "初始"
    chart.set_title("新标题")
    assert chart._figure.axes[0].get_title() == "新标题"


def test_invalid_json_falls_back_to_empty(qapp) -> None:
    chart = ChartComponent("c2", "demo.obox", {"data": "not json"})
    assert chart.data() == "{}"


def test_x_labels_applied(qapp) -> None:
    chart = _chart(
        {
            "type": "bar",
            "series": [{"name": "甲", "points": [{"x": 0, "y": 1}, {"x": 1, "y": 2}]}],
            "x": ["一月", "二月"],
        }
    )
    labels = [tick.get_text() for tick in chart._figure.axes[0].get_xticklabels()]
    assert labels == ["一月", "二月"]
