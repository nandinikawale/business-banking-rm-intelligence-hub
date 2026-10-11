import pandas as pd
import pytest

from rm_hub.services.opportunities import (
    filter_opportunities,
    opportunity_breakdown,
    opportunity_summary,
)


@pytest.fixture
def worklist():
    return pd.DataFrame(
        [
            {
                "customer_id": "A",
                "rm_id": "RM1",
                "rm_name": "Fictional RM1",
                "signal_type": "Cross-sell",
                "product": "credit_card",
                "priority": 2,
            },
            {
                "customer_id": "A",
                "rm_id": "RM1",
                "rm_name": "Fictional RM1",
                "signal_type": "Retention",
                "product": "Deposit relationship",
                "priority": 1,
            },
            {
                "customer_id": "B",
                "rm_id": "RM2",
                "rm_name": "Fictional RM2",
                "signal_type": "Cross-sell",
                "product": "payroll_services",
                "priority": 2,
            },
        ]
    )


def test_signal_count_is_not_customer_count(worklist):
    assert opportunity_summary(worklist) == {
        "signal_count": 3,
        "customer_count": 2,
        "retention_signal_count": 1,
        "cross_sell_signal_count": 2,
    }


def test_filters_and_default_order(worklist):
    assert filter_opportunities(worklist).priority.tolist() == [1, 2, 2]
    assert len(filter_opportunities(worklist, "Cross-sell", "credit_card")) == 1
    empty = filter_opportunities(worklist, "Retention", "credit_card")
    assert empty.empty
    assert opportunity_summary(empty)["customer_count"] == 0
    with pytest.raises(ValueError):
        filter_opportunities(worklist, "Unknown")


@pytest.mark.parametrize("by", ["rm", "product"])
def test_breakdowns_reconcile_to_signal_count(worklist, by):
    result = opportunity_breakdown(worklist, by)
    assert result.signal_count.sum() == 3
    assert result.groupby("signal_type").signal_count.sum().to_dict() == {
        "Cross-sell": 2,
        "Retention": 1,
    }
    assert opportunity_breakdown(worklist.iloc[:0], by).empty


def test_reject_unknown_breakdown(worklist):
    with pytest.raises(ValueError):
        opportunity_breakdown(worklist, "unknown")
