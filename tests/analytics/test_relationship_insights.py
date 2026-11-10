import pandas as pd
import pytest

from rm_hub.data.repository import Filters
from rm_hub.services.relationship_insights import (
    deposit_contributors,
    deposit_movement,
    profitability_breakdown,
)


def test_deposit_movement_reconciles_with_source_csv(repository, dataset):
    result = deposit_movement(repository, "2025-12-01")
    source = dataset[1]["deposits"]
    expected = (
        (
            source.query("month == '2025-12-01'")
            .set_index("customer_id")
            .closing_balance
            - source.query("month == '2025-11-01'")
            .set_index("customer_id")
            .closing_balance
        )
        .round(2)
        .sort_index()
    )
    actual = result["details"].set_index("customer_id").deposit_change.sort_index()
    assert actual.tolist() == pytest.approx(expected.tolist())
    assert result["net_change"] == pytest.approx(expected.sum())
    assert result["increases"] + result["decreases"] == pytest.approx(
        result["net_change"]
    )
    assert result["current_balance"] - result["previous_balance"] == pytest.approx(
        result["net_change"]
    )
    shown = deposit_contributors(result["details"], per_direction=2)
    assert shown.deposit_change.sum() == pytest.approx(result["net_change"])
    assert shown.customer_count.sum() == len(result["details"])


def test_movement_uses_same_filters_and_handles_missing_baseline(repository, dataset):
    customer = dataset[1]["customers"].iloc[0]
    result = deposit_movement(
        repository,
        "2024-06-01",
        Filters(
            rm_id=customer.rm_id,
            industry=customer.industry,
            region=customer.region,
        ),
    )
    assert result["details"].rm_name.nunique() == 1
    assert result["details"].industry.eq(customer.industry).all()
    assert result["details"].region.eq(customer.region).all()
    assert result["previous_month"] == pd.Timestamp("2024-05-01").date()
    first = deposit_movement(repository, "2024-01-01")
    assert not first["available"]
    assert first["net_change"] is None
    assert first["details"].empty
    empty = deposit_movement(repository, filters=Filters(rm_id="UNKNOWN"))
    assert empty["details"].empty
    assert empty["net_change"] == 0


def test_zero_baseline_and_offsetting_movements():
    class Fixture:
        def resolve_month(self, month):
            return pd.Timestamp("2024-02-01").date()

        def periods(self):
            return [
                pd.Timestamp(value).date() for value in ["2024-01-01", "2024-02-01"]
            ]

        def snapshot(self, month, filters):
            values = [100, 0, 40, 30] if month.month == 1 else [70, 50, 20, 30]
            return pd.DataFrame(
                {
                    "customer_id": list("ABCD"),
                    "business_name": list("ABCD"),
                    "rm_name": ["RM"] * 4,
                    "industry": ["Industry"] * 4,
                    "region": ["Region"] * 4,
                    "deposit_balance": values,
                }
            )

    result = deposit_movement(Fixture())
    assert result["net_change"] == 0
    assert result["increases"] == 50
    assert result["decreases"] == -50
    rows = result["details"].set_index("customer_id")
    assert rows.loc["A", "deposit_change_percent"] == -30
    assert pd.isna(rows.loc["B", "deposit_change_percent"])
    contributors = deposit_contributors(result["details"], 1)
    assert contributors.deposit_change.sum() == 0
    assert contributors.customer_count.sum() == 4
    assert contributors.label.tolist() == ["A", "B", "Other customers (net)"]


def profit_fixture():
    current = {
        "month": pd.Timestamp("2024-02-01"),
        "deposit_revenue": 100,
        "lending_revenue": 200,
        "card_revenue": 30,
        "service_fee_revenue": 70,
        "servicing_expense": 40,
        "loan_funding_expense": 50,
        "card_funding_expense": 10,
        "credit_cost_expense": 20,
        "total_revenue": 400,
        "allocated_expenses": 120,
        "profitability": 280,
        "deposit_interest_expense": 999,
    }
    previous = {
        **current,
        "month": pd.Timestamp("2024-01-01"),
        "deposit_revenue": 150,
        "servicing_expense": 20,
        "total_revenue": 450,
        "allocated_expenses": 100,
        "profitability": 350,
    }
    future = {**current, "month": pd.Timestamp("2024-03-01"), "profitability": 99999}
    return pd.DataFrame([previous, current, future])


def test_profit_components_and_changes_exclude_future_and_double_deduction():
    result = profitability_breakdown(profit_fixture(), "2024-02-01")
    rows = result["components"].set_index("key")
    assert result["has_previous"]
    assert rows.loc["profitability", "current"] == 280
    assert rows.loc["profitability", "change"] == -70
    detail = result["components"].query("kind != 'Total'")
    assert detail.profit_impact.sum() == -70
    assert rows.loc["servicing_expense", "change"] == 20
    assert rows.loc["servicing_expense", "profit_impact"] == -20
    assert "deposit_interest_expense" not in rows.index


def test_profit_first_month_missing_calendar_month_and_invalid_reconciliation():
    history = profit_fixture()
    first = profitability_breakdown(history, "2024-01-01")
    assert not first["has_previous"]
    assert first["components"].previous.isna().all()
    assert first["components"].change.isna().all()
    gap = profitability_breakdown(history.iloc[[1]], "2024-02-01")
    assert not gap["has_previous"]
    history.loc[1, "total_revenue"] = 1000
    with pytest.raises(ValueError, match="reconcile"):
        profitability_breakdown(history, "2024-02-01")


def test_profit_breakdown_matches_generated_csv(repository, dataset):
    customer_id = dataset[1]["customers"].customer_id.iloc[0]
    history = repository.history(customer_id=customer_id, end="2024-06-01")
    result = profitability_breakdown(history, "2024-06-01")
    expected = (
        dataset[1]["profitability"]
        .query("customer_id == @customer_id and month == '2024-06-01'")
        .iloc[0]
    )
    rows = result["components"].set_index("key")
    for key in rows.index:
        assert rows.loc[key, "current"] == pytest.approx(expected[key])
