"""Explainable deposit movements and bank relationship profitability."""

import pandas as pd

from rm_hub.data.repository import month_date

MOVEMENT_COLUMNS = [
    "customer_id",
    "business_name",
    "rm_name",
    "industry",
    "region",
    "previous_balance",
    "current_balance",
    "deposit_change",
    "deposit_change_percent",
]
REVENUES = {
    "deposit_revenue": "Deposit revenue",
    "lending_revenue": "Lending revenue",
    "card_revenue": "Card revenue",
    "service_fee_revenue": "Service revenue",
}
COSTS = {
    "servicing_expense": "Servicing expense",
    "loan_funding_expense": "Loan funding expense",
    "card_funding_expense": "Card funding expense",
    "credit_cost_expense": "Credit cost allocation",
}


def deposit_movement(repository, month=None, filters=None):
    """Compare closing balances for the same filtered customers in adjacent months."""
    selected = repository.resolve_month(month)
    previous_month = (pd.Timestamp(selected) - pd.offsets.MonthBegin()).date()
    current = repository.snapshot(selected, filters)
    current_balance = round(float(current.deposit_balance.sum()), 2)
    result = {
        "month": selected,
        "previous_month": previous_month,
        "available": previous_month in repository.periods(),
        "current_balance": current_balance,
        "previous_balance": None,
        "increases": None,
        "decreases": None,
        "net_change": None,
        "details": pd.DataFrame(columns=MOVEMENT_COLUMNS),
    }
    if not result["available"]:
        return result
    previous = repository.snapshot(previous_month, filters)
    baseline = previous[["customer_id", "deposit_balance"]].rename(
        columns={"deposit_balance": "previous_balance"}
    )
    details = (
        current[
            [
                "customer_id",
                "business_name",
                "rm_name",
                "industry",
                "region",
                "deposit_balance",
            ]
        ]
        .rename(columns={"deposit_balance": "current_balance"})
        .merge(
            baseline,
            on="customer_id",
            how="outer",
            validate="one_to_one",
            indicator=True,
        )
    )
    if not details["_merge"].eq("both").all():
        raise ValueError("Deposit comparison requires matching customer coverage")
    details["deposit_change"] = (
        details.current_balance - details.previous_balance
    ).round(2)
    details["deposit_change_percent"] = (
        details.deposit_change.div(
            details.previous_balance.where(details.previous_balance.ne(0))
        )
        .mul(100)
        .round(2)
    )
    details = (
        details[MOVEMENT_COLUMNS]
        .sort_values(["deposit_change", "customer_id"], ascending=[True, True])
        .reset_index(drop=True)
    )
    result.update(
        previous_balance=round(float(previous.deposit_balance.sum()), 2),
        increases=round(
            float(details.loc[details.deposit_change.gt(0), "deposit_change"].sum()), 2
        ),
        decreases=round(
            float(details.loc[details.deposit_change.lt(0), "deposit_change"].sum()), 2
        ),
        net_change=round(float(details.deposit_change.sum()), 2),
        details=details,
    )
    return result


def deposit_contributors(details, per_direction=5):
    """Show largest increases/decreases plus the net of all remaining customers."""
    if per_direction < 1:
        raise ValueError("At least one contributor per direction is required")
    decreases = details[details.deposit_change.lt(0)].nsmallest(
        per_direction, "deposit_change", keep="first"
    )
    increases = details[details.deposit_change.gt(0)].nlargest(
        per_direction, "deposit_change", keep="first"
    )
    shown = pd.concat([decreases, increases])
    rows = [
        {
            "label": row.customer_id,
            "business_name": row.business_name,
            "deposit_change": row.deposit_change,
            "customer_count": 1,
        }
        for row in shown.itertuples()
    ]
    remaining = details[~details.customer_id.isin(shown.customer_id)]
    if len(remaining):
        rows.append(
            {
                "label": "Other customers (net)",
                "business_name": "All customers outside the displayed largest movers",
                "deposit_change": round(float(remaining.deposit_change.sum()), 2),
                "customer_count": len(remaining),
            }
        )
    return pd.DataFrame(
        rows, columns=["label", "business_name", "deposit_change", "customer_count"]
    )


def profitability_breakdown(history, month):
    """Decompose bank profit; prior comparisons use the preceding calendar month only."""
    selected = pd.Timestamp(month_date(month))
    current = history.loc[history.month.eq(selected)]
    if len(current) != 1:
        raise ValueError(
            "Profitability requires one customer observation for the month"
        )
    current = current.iloc[0]
    prior_month = selected - pd.offsets.MonthBegin()
    previous_rows = history.loc[history.month.eq(prior_month)]
    previous = previous_rows.iloc[0] if len(previous_rows) == 1 else None
    rows = []
    totals = {
        "total_revenue": "Total bank revenue",
        "allocated_expenses": "Allocated expenses",
        "profitability": "Bank profitability",
    }
    for key, label in {**REVENUES, **COSTS, **totals}.items():
        amount = round(float(current[key]), 2)
        prior = None if previous is None else round(float(previous[key]), 2)
        change = None if prior is None else round(amount - prior, 2)
        kind = "Revenue" if key in REVENUES else "Cost" if key in COSTS else "Total"
        rows.append(
            {
                "key": key,
                "component": label,
                "kind": kind,
                "current": amount,
                "previous": prior,
                "change": change,
                "profit_impact": None
                if change is None
                else (
                    -change if key in COSTS or key == "allocated_expenses" else change
                ),
            }
        )
    components = pd.DataFrame(rows)
    revenue_sum = round(sum(float(current[key]) for key in REVENUES), 2)
    cost_sum = round(sum(float(current[key]) for key in COSTS), 2)
    for actual, expected in [
        (revenue_sum, current.total_revenue),
        (cost_sum, current.allocated_expenses),
        (round(revenue_sum - cost_sum, 2), current.profitability),
    ]:
        if abs(actual - float(expected)) > 0.011:
            raise ValueError("Bank profitability components do not reconcile")
    return {
        "month": selected.date(),
        "previous_month": prior_month.date(),
        "has_previous": previous is not None,
        "components": components,
    }
