import json
from datetime import date

import pytest


@pytest.fixture
def customer_app(app):
    return app.switch_page("views/customer_360.py").run()


def test_initial_customer_page(customer_app, ui_dataset):
    app = customer_app
    assert not app.exception
    assert not app.error
    assert any(title.value == "Customer 360" for title in app.title)
    assert app.selectbox(key="customer_month").value == date(2025, 12, 1)
    assert (
        app.selectbox(key="customer_id").value
        == ui_dataset[1]["customers"].customer_id.iloc[0]
    )
    assert len(app.metric) == 11
    assert len(app.get("plotly_chart")) == 3
    assert app.dataframe[-1].value.shape[0] == 24


def test_switch_customer_updates_profile_and_finances(customer_app, ui_dataset):
    app = customer_app
    customer = ui_dataset[1]["customers"].iloc[1]
    app.selectbox(key="customer_id").set_value(customer.customer_id).run()
    assert not app.exception
    assert any(item.value == customer.business_name for item in app.subheader)
    expected = (
        ui_dataset[1]["profitability"]
        .query("customer_id == @customer.customer_id and month == '2025-12-01'")
        .profitability.iloc[0]
    )
    assert app.dataframe[-1].value["Bank profitability (USD)"].iloc[
        -1
    ] == pytest.approx(expected)


def test_historical_month_has_no_future_data(customer_app):
    app = customer_app
    month = date(2024, 6, 1)
    app.selectbox(key="customer_month").set_value(month).run()
    assert not app.exception
    table = app.dataframe[-1].value
    assert len(table) == 6
    assert table.Month.iloc[-1] == "2024-06"
    for element in app.get("plotly_chart"):
        figure = json.loads(element.proto.spec)
        assert date.fromisoformat(figure["layout"]["xaxis"]["range"][-1]) <= month
        for trace in figure["data"]:
            assert len(trace["x"]) == 6
            assert all(date.fromisoformat(value) <= month for value in trace["x"])


@pytest.mark.parametrize(
    "flag,index,product",
    [("has_loan", 1, "Loans"), ("has_credit_card", 2, "Credit cards")],
)
def test_nonholders_display_zero_and_not_held(
    customer_app, ui_dataset, flag, index, product
):
    app = customer_app
    products = ui_dataset[1]["products"].query("month == '2025-12-01'")
    customer_id = products.loc[~products[flag], "customer_id"].iloc[0]
    app.selectbox(key="customer_id").set_value(customer_id).run()
    assert not app.exception
    assert app.metric[index].value == "$0.00"
    holdings = app.dataframe[0].value.set_index("Product")
    assert holdings.loc[product, "Status"] == "Not held"


def test_historical_view_hides_future_product_adoption(customer_app, ui_dataset):
    products = ui_dataset[1]["products"]
    customer_ids = []
    for customer_id, frame in products.groupby("customer_id"):
        if frame.has_payroll_services.nunique() > 1:
            customer_ids.append(customer_id)
    assert customer_ids
    app = customer_app
    app.selectbox(key="customer_id").set_value(customer_ids[0])
    app.selectbox(key="customer_month").set_value(date(2024, 12, 1)).run()
    assert not app.exception
    assert any("No product changes" in caption.value for caption in app.caption)
    app.selectbox(key="customer_month").set_value(date(2025, 1, 1)).run()
    assert not app.exception
    changes = [
        table.value for table in app.dataframe if "Change" in table.value.columns
    ]
    assert len(changes) == 1
    assert changes[0].Month.tolist() == ["January 2025"]
    assert changes[0].Product.tolist() == ["Payroll services"]


def test_first_month_requires_more_history(customer_app):
    app = customer_app
    app.selectbox(key="customer_month").set_value(date(2024, 1, 1)).run()
    assert not app.exception
    assert any(
        "At least four monthly observations" in message.value for message in app.info
    )
    assert not app.warning


def test_missing_data_on_customer_page(monkeypatch, tmp_path):
    from streamlit.testing.v1 import AppTest

    from rm_hub.settings import PROJECT_ROOT

    monkeypatch.setenv("RM_HUB_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(
        str(PROJECT_ROOT / "streamlit_app" / "app.py"), default_timeout=60
    ).run()
    app.switch_page("views/customer_360.py").run()
    assert not app.exception
    assert app.error
    assert "Missing synthetic data files" in app.error[0].value
    assert "banking-data generate" in app.code[0].value
