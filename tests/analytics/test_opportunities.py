import pandas as pd

from rm_hub.data.repository import Filters
from rm_hub.services.opportunities import opportunities


def test_signals_match_csv_indicators(repository, dataset):
    result = opportunities(repository)
    tables = dataset[1]
    mapping = {
        "merchant_cross_sell": "merchant_services",
        "payroll_cross_sell": "payroll_services",
        "treasury_cross_sell": "treasury_services",
        "card_cross_sell": "credit_card",
    }
    latest = tables["products"].query("month == '2025-12-01'")
    for signal, product in mapping.items():
        expected = set(latest.loc[latest[signal], "customer_id"])
        actual = set(
            result.loc[
                (result.signal_type == "Cross-sell") & (result["product"] == product),
                "customer_id",
            ]
        )
        assert actual == expected
    deposits = tables["deposits"].query("month == '2025-12-01'")
    assert set(result.loc[result.signal_type == "Retention", "customer_id"]) == set(
        deposits.loc[deposits.attrition_indicator, "customer_id"]
    )
    assert result.reason.str.len().gt(0).all()
    assert result.priority.is_monotonic_increasing
    filtered = opportunities(repository, filters=Filters(rm_id="SYN-RM001"))
    assert filtered.rm_id.eq("SYN-RM001").all()
    assert opportunities(repository, filters=Filters(rm_id="UNKNOWN")).empty


def test_historical_signals_do_not_use_future_months(repository, dataset):
    result = opportunities(repository, "2024-01-01")
    assert not result.signal_type.eq("Retention").any()
    latest = dataset[1]["products"].query("month == '2024-01-01'")
    assert set(result.loc[result["product"] == "credit_card", "customer_id"]) == set(
        latest.loc[latest.card_cross_sell, "customer_id"]
    )


def test_independent_threshold_and_decline_fixture():
    class FixtureRepository:
        def resolve_month(self, month):
            return pd.Timestamp("2024-04-01").date()

        def history(self, **kwargs):
            rows = []
            for month, balance in zip(
                pd.date_range("2024-01-01", periods=4, freq="MS"),
                [10000, 9000, 8500, 8000],
            ):
                rows.append(
                    {
                        "customer_id": "FICTIONAL",
                        "business_name": "Fictional fixture",
                        "rm_id": "RM",
                        "rm_name": "Fictional RM",
                        "month": month,
                        "deposit_balance": balance,
                        "business_revenue": 50000,
                        "has_merchant_services": False,
                        "has_payroll_services": False,
                        "has_treasury_services": True,
                        "has_credit_card": True,
                    }
                )
            return pd.DataFrame(rows)

    result = opportunities(FixtureRepository())
    assert result.signal_type.tolist() == ["Retention", "Cross-sell"]
    assert result["product"].tolist() == ["Deposit relationship", "merchant_services"]
    assert result.iloc[0].deposit_change_percent == -20
    assert result.iloc[1].threshold == 50000


def test_customer_scoped_signals_match_portfolio_subset(repository):
    customer_id = repository.customers().customer_id.iloc[0]
    all_signals = opportunities(repository)
    expected = all_signals[all_signals.customer_id == customer_id].reset_index(
        drop=True
    )
    actual = opportunities(repository, customer_id=customer_id)
    pd.testing.assert_frame_equal(actual, expected)


def test_empty_customer_signal_schema_matches_portfolio(repository):
    expected = opportunities(repository).iloc[:0].reset_index(drop=True)
    actual = opportunities(repository, customer_id="UNKNOWN")
    pd.testing.assert_frame_equal(actual, expected)
