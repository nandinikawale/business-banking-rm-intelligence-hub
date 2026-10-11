import itertools

import pandas as pd

COLUMNS = [
    "customer_id",
    "business_name",
    "rm_id",
    "rm_name",
    "month",
    "signal_type",
    "product",
    "priority",
    "activity_value",
    "threshold",
    "deposit_change_percent",
    "reason",
]
RULES = [
    ("merchant_services", "has_merchant_services", "business_revenue", 50000),
    ("payroll_services", "has_payroll_services", "business_revenue", 80000),
    ("treasury_services", "has_treasury_services", "deposit_balance", 200000),
    ("credit_card", "has_credit_card", "business_revenue", 25000),
]


def opportunities(repository, month=None, filters=None, customer_id=None):
    """Transparent rules using observations up to the selected month only."""
    selected = repository.resolve_month(month)
    history = repository.history(filters=filters, end=selected, customer_id=customer_id)
    current = history[history.month == pd.Timestamp(selected)]
    rows = []
    for _, customer in current.iterrows():
        base = {
            column: customer[column]
            for column in ["customer_id", "business_name", "rm_id", "rm_name", "month"]
        }
        window = history[history.customer_id == customer.customer_id].tail(4)
        balances = window.deposit_balance.tolist()
        periods = window.month.dt.to_period("M").astype("int64").tolist()
        consecutive = len(periods) == 4 and all(
            b - a == 1 for a, b in itertools.pairwise(periods)
        )
        if consecutive:
            a, b, c, d = balances
            if a >= 10000 and a > b > c > d and d <= a * 0.8:
                decline = round((d / a - 1) * 100, 2)
                rows.append(
                    {
                        **base,
                        "signal_type": "Retention",
                        "product": "Deposit relationship",
                        "priority": 1,
                        "activity_value": d,
                        "threshold": 20,
                        "deposit_change_percent": decline,
                        "reason": f"Deposits fell {abs(decline):.2f}% across three consecutive declines; starting balance USD {a:,.2f}.",
                    }
                )
        for product, holding, activity, threshold in RULES:
            if not customer[holding] and customer[activity] >= threshold:
                label = (
                    "closing deposits"
                    if activity == "deposit_balance"
                    else "monthly business sales"
                )
                rows.append(
                    {
                        **base,
                        "signal_type": "Cross-sell",
                        "product": product,
                        "priority": 2,
                        "activity_value": customer[activity],
                        "threshold": threshold,
                        "deposit_change_percent": None,
                        "reason": f"Missing {product.replace('_', ' ')}; {label} USD {customer[activity]:,.2f} meet the fictional USD {threshold:,.0f} threshold.",
                    }
                )
    return (
        pd.DataFrame(rows, columns=COLUMNS)
        .astype(
            {
                "month": "datetime64[ns]",
                "priority": "int64",
                "activity_value": "float64",
                "threshold": "float64",
                "deposit_change_percent": "float64",
            }
        )
        .sort_values(["priority", "rm_id", "customer_id", "product"])
        .reset_index(drop=True)
    )


def filter_opportunities(signals, signal_type=None, product=None):
    """Filter an observed worklist while retaining the documented review order."""
    if signal_type not in (None, "Retention", "Cross-sell"):
        raise ValueError("Signal type must be Retention or Cross-sell")
    result = signals
    if signal_type is not None:
        result = result[result.signal_type == signal_type]
    if product is not None:
        result = result[result["product"] == product]
    return result.sort_values(
        ["priority", "rm_id", "customer_id", "product"]
    ).reset_index(drop=True)


def opportunity_summary(signals):
    return {
        "signal_count": len(signals),
        "customer_count": int(signals.customer_id.nunique()),
        "retention_signal_count": int(signals.signal_type.eq("Retention").sum()),
        "cross_sell_signal_count": int(signals.signal_type.eq("Cross-sell").sum()),
    }


def opportunity_breakdown(signals, by):
    keys = {"rm": ["rm_id", "rm_name"], "product": ["product"]}
    if by not in keys:
        raise ValueError("Breakdown must be rm or product")
    return (
        signals.groupby([*keys[by], "signal_type"], as_index=False)
        .size()
        .rename(columns={"size": "signal_count"})
    )
