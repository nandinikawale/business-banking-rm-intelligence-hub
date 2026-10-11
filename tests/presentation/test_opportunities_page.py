from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from rm_hub.settings import PROJECT_ROOT


@pytest.fixture
def opportunities_app(app):
    return app.switch_page("views/rm_opportunities.py").run()


def counts_from_csv(tables, month, ids=None):
    products = tables["products"][tables["products"].month == month]
    deposits = tables["deposits"][tables["deposits"].month == month]
    if ids is not None:
        products = products[products.customer_id.isin(ids)]
        deposits = deposits[deposits.customer_id.isin(ids)]
    cross_columns = [
        "merchant_cross_sell",
        "payroll_cross_sell",
        "treasury_cross_sell",
        "card_cross_sell",
    ]
    cross_count = int(products[cross_columns].sum().sum())
    retention_count = int(deposits.attrition_indicator.sum())
    customers = set(products.loc[products[cross_columns].any(axis=1), "customer_id"])
    customers.update(deposits.loc[deposits.attrition_indicator, "customer_id"])
    return cross_count + retention_count, len(customers), retention_count, cross_count


def metric_counts(app):
    return tuple(int(metric.value.replace(",", "")) for metric in app.metric)


def test_initial_page_counts_and_order(opportunities_app, ui_dataset):
    app = opportunities_app
    assert not app.exception
    assert not app.error
    assert any(title.value == "RM Opportunities" for title in app.title)
    assert app.selectbox(key="opp_month").value == date(2025, 12, 1)
    assert metric_counts(app) == counts_from_csv(ui_dataset[1], "2025-12-01")
    assert len(app.get("plotly_chart")) == 2
    table = app.dataframe[0].value
    assert len(table) == metric_counts(app)[0]
    assert table["Customer ID"].nunique() == metric_counts(app)[1]
    assert table["Review order"].tolist() == sorted(table["Review order"].tolist())
    assert table["Supporting observation"].str.len().gt(0).all()
    retention = table[table["Signal type"] == "Retention"]
    cross_sell = table[table["Signal type"] == "Cross-sell"]
    assert retention["Rule threshold"].str.contains("%").all()
    assert not retention["Rule threshold"].str.contains("USD").any()
    assert cross_sell["Rule threshold"].str.contains("USD").all()


def test_population_filters_update_all_counts(opportunities_app, ui_dataset):
    app = opportunities_app
    customers = ui_dataset[1]["customers"]
    target = customers.iloc[0]
    app.selectbox(key="opp_rm").set_value(target.rm_id)
    app.selectbox(key="opp_industry").set_value(target.industry)
    app.selectbox(key="opp_region").set_value(target.region).run()
    assert not app.exception
    ids = customers.loc[
        (customers.rm_id == target.rm_id)
        & (customers.industry == target.industry)
        & (customers.region == target.region),
        "customer_id",
    ]
    assert metric_counts(app) == counts_from_csv(ui_dataset[1], "2025-12-01", ids)
    if app.dataframe:
        assert app.dataframe[0].value["Customer ID"].isin(ids).all()


def test_product_and_signal_filters(opportunities_app, ui_dataset):
    app = opportunities_app
    app.selectbox(key="opp_type").set_value("Cross-sell")
    app.selectbox(key="opp_product").set_value("credit_card").run()
    assert not app.exception
    latest = ui_dataset[1]["products"].query("month == '2025-12-01'")
    expected = int(latest.card_cross_sell.sum())
    assert metric_counts(app) == (expected, expected, 0, expected)
    assert app.dataframe[0].value["Potential product"].eq("Credit card").all()
    assert app.dataframe[0].value["Signal type"].eq("Cross-sell").all()


def test_empty_selection_is_clear_and_zero(opportunities_app):
    app = opportunities_app
    app.selectbox(key="opp_type").set_value("Retention")
    app.selectbox(key="opp_product").set_value("credit_card").run()
    assert not app.exception
    assert metric_counts(app) == (0, 0, 0, 0)
    assert any("No signals match" in message.value for message in app.info)
    assert not app.dataframe
    assert not app.get("plotly_chart")


def test_historical_month_excludes_future_signals(opportunities_app, ui_dataset):
    app = opportunities_app
    app.selectbox(key="opp_month").set_value(date(2024, 1, 1)).run()
    assert not app.exception
    assert metric_counts(app) == counts_from_csv(ui_dataset[1], "2024-01-01")
    assert metric_counts(app)[2] == 0
    assert app.dataframe[0].value["Reporting month"].eq("January 2024").all()


def test_missing_data_on_opportunities_page(monkeypatch, tmp_path):
    monkeypatch.setenv("RM_HUB_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(
        str(PROJECT_ROOT / "streamlit_app" / "app.py"), default_timeout=60
    ).run()
    app.switch_page("views/rm_opportunities.py").run()
    assert not app.exception
    assert app.error
    assert "Missing synthetic data files" in app.error[0].value
    assert "banking-data generate" in app.code[0].value
