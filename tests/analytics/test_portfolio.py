import pytest

from rm_hub.data.repository import Filters
from rm_hub.services.portfolio import concentration, portfolio_summary, portfolio_trends


def test_summary_independent_csv_totals(repository, dataset):
    tables = dataset[1]
    summary = portfolio_summary(repository, "2025-12-01")
    assert summary["customer_count"] == 30
    for source, metric in [
        ("deposits", "deposit_balance"),
        ("loans", "loan_balance"),
        ("credit_cards", "card_balance"),
    ]:
        current = tables[source].query("month == '2025-12-01'").closing_balance.sum()
        previous = tables[source].query("month == '2025-11-01'").closing_balance.sum()
        assert summary[metric] == pytest.approx(current)
        assert summary["month_over_month"][metric]["absolute"] == pytest.approx(
            round(current - previous, 2)
        )
    profits = tables["profitability"].query("month == '2025-12-01'").profitability.sum()
    assert summary["profitability"] == pytest.approx(profits)
    assert summary["product_penetration_percent"]["has_loan"] == pytest.approx(
        round(
            tables["products"].query("month == '2025-12-01'").has_loan.mean() * 100, 2
        )
    )


def test_trends_do_not_sum_balances_over_time(repository, dataset):
    trends = portfolio_trends(repository)
    assert len(trends) == 24
    expected = dataset[1]["deposits"].groupby("month").closing_balance.sum()
    assert trends.deposit_balance.tolist() == pytest.approx(expected.tolist())
    assert len(portfolio_trends(repository, start="2025-01-01", end="2025-03-01")) == 3


def test_concentration_and_empty_selection(repository):
    grouped = concentration(repository, group_by="rm_id")
    assert grouped.customer_count.sum() == 30
    assert grouped.deposit_share_percent.sum() == pytest.approx(100)
    with pytest.raises(ValueError, match="Group by"):
        concentration(repository, group_by="customer_id")
    empty = portfolio_summary(repository, filters=Filters(rm_id="UNKNOWN"))
    assert empty["customer_count"] == 0
    assert empty["deposit_balance"] == 0
    assert empty["month_over_month"]["deposit_balance"]["percent"] is None
    assert concentration(repository, filters=Filters(rm_id="UNKNOWN")).empty


def test_first_month_has_no_comparison(repository):
    result = portfolio_summary(repository, "2024-01-01")
    assert result["month_over_month"]["deposit_balance"] == {
        "absolute": None,
        "percent": None,
    }
