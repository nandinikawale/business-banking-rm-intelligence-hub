import json
from datetime import date

from streamlit.testing.v1 import AppTest

from rm_hub.settings import PROJECT_ROOT


def test_initial_page(app):
    assert not app.exception
    assert not app.error
    assert any(title.value == "Portfolio Overview" for title in app.title)
    assert app.selectbox(key="reporting_month").value == date(2025, 12, 1)
    assert len(app.metric) == 8
    assert app.metric[0].label == "Customers"
    assert app.metric[0].value == "30"
    assert len(app.get("plotly_chart")) == 5
    assert len(app.dataframe) == 2
    assert any("Entirely fictional" in item.value for item in app.caption)


def test_rm_filter_updates_population(app, ui_dataset):
    app.selectbox(key="rm_filter").set_value("SYN-RM001").run()
    assert not app.exception
    expected = int((ui_dataset[1]["customers"].rm_id == "SYN-RM001").sum())
    assert app.metric[0].value == str(expected)
    customer_table = app.dataframe[1].value
    assert customer_table["Relationship manager"].eq("Fictional RM 001").all()


def test_month_selection_prevents_future_chart_data(app):
    selected = date(2024, 6, 1)
    app.selectbox(key="reporting_month").set_value(selected).run()
    assert not app.exception
    for element in app.get("plotly_chart")[:2]:
        figure = json.loads(element.proto.spec)
        assert date.fromisoformat(figure["layout"]["xaxis"]["range"][-1]) <= selected
        for trace in figure["data"]:
            assert len(trace["x"]) == 6
            assert all(date.fromisoformat(value) <= selected for value in trace["x"])


def test_empty_filter_combination(app):
    app.selectbox(key="rm_filter").set_value("SYN-RM001")
    app.selectbox(key="region_filter").set_value("Region 2").run()
    assert not app.exception
    assert any("No customers match" in message.value for message in app.info)
    assert not app.metric
    assert not app.get("plotly_chart")


def test_first_month_has_no_misleading_delta(app):
    app.selectbox(key="reporting_month").set_value(date(2024, 1, 1)).run()
    assert not app.exception
    assert app.metric[1].delta == ""


def test_missing_data_has_actionable_error(monkeypatch, tmp_path):
    monkeypatch.setenv("RM_HUB_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(
        str(PROJECT_ROOT / "streamlit_app" / "app.py"), default_timeout=30
    ).run()
    assert not app.exception
    assert app.error
    assert "Missing synthetic data files" in app.error[0].value
    assert "banking-data generate" in app.code[0].value
    assert not app.metric
