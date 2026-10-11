import pandas as pd

BALANCES = ["deposit_balance", "loan_balance", "card_balance"]
FLOWS = ["total_revenue", "allocated_expenses", "profitability"]
HOLDINGS = [
    "has_deposit_account",
    "has_loan",
    "has_credit_card",
    "has_merchant_services",
    "has_payroll_services",
    "has_treasury_services",
]


def portfolio_summary(repository, month=None, filters=None):
    selected = repository.resolve_month(month)
    current = repository.snapshot(selected, filters)
    previous_month = (pd.Timestamp(selected) - pd.offsets.MonthBegin()).date()
    previous = (
        repository.snapshot(previous_month, filters)
        if previous_month in repository.periods()
        else None
    )
    totals = {
        column: round(float(current[column].sum()), 2) for column in BALANCES + FLOWS
    }
    changes = {}
    for column, total in totals.items():
        baseline = (
            None
            if previous is None or previous.empty
            else round(float(previous[column].sum()), 2)
        )
        changes[column] = {
            "absolute": None if baseline is None else round(total - baseline, 2),
            "percent": None
            if baseline in (None, 0)
            else round((total - baseline) / baseline * 100, 2),
        }
    return {
        "month": selected,
        "customer_count": len(current),
        **totals,
        "attrition_customer_count": int(current.attrition_indicator.sum()),
        "product_penetration_percent": {
            column: round(float(current[column].mean()) * 100, 2)
            if len(current)
            else 0.0
            for column in HOLDINGS
        },
        "month_over_month": changes,
    }


def portfolio_trends(repository, filters=None, start=None, end=None):
    history = repository.history(filters=filters, start=start, end=end)
    return (
        history.groupby("month", as_index=False)
        .agg(
            **{column: (column, "sum") for column in BALANCES + FLOWS},
            customer_count=("customer_id", "nunique"),
            attrition_customer_count=("attrition_indicator", "sum"),
        )
        .sort_values("month")
        .reset_index(drop=True)
    )


def concentration(repository, month=None, filters=None, group_by="industry"):
    if group_by not in ("industry", "rm_id", "region"):
        raise ValueError("Group by industry, rm_id, or region")
    frame = repository.snapshot(month, filters)
    result = frame.groupby(group_by, as_index=False).agg(
        customer_count=("customer_id", "nunique"),
        **{column: (column, "sum") for column in BALANCES + FLOWS},
    )
    total = float(result.deposit_balance.sum())
    result["deposit_share_percent"] = (
        result.deposit_balance / total * 100 if total else 0.0
    )
    return result.sort_values(
        ["deposit_balance", group_by], ascending=[False, True]
    ).reset_index(drop=True)
