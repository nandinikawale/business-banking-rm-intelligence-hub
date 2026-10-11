import numpy as np
import pandas as pd

from .indicators import sustained_decline

MONTHLY = ("deposits", "loans", "credit_cards", "profitability", "products")


def validate(tables, config):
    def check(condition, message):
        if not bool(condition):
            raise ValueError(message)

    def equals(a, b, message):
        check(np.allclose(a, b, atol=0.011, rtol=0), message)

    customers = tables["customers"]
    check(len(customers) == config.customers, "Customer count")
    check(customers.customer_id.is_unique, "Duplicate customers")
    check(tables["relationship_managers"].rm_id.is_unique, "Duplicate RMs")
    check(
        customers.rm_id.isin(tables["relationship_managers"].rm_id).all(), "Unknown RM"
    )
    check(customers.is_synthetic.all(), "Synthetic flag")
    expected = pd.MultiIndex.from_product(
        [
            sorted(customers.customer_id),
            pd.date_range(config.start, config.end, freq="MS").strftime("%Y-%m-%d"),
        ],
        names=["customer_id", "month"],
    )
    normalized = {}
    for name in MONTHLY:
        frame = tables[name]
        check(not frame.isna().any().any(), f"{name}: null values")
        idx = frame.set_index(["customer_id", "month"]).sort_index()
        check(
            idx.index.is_unique and idx.index.equals(expected),
            f"{name}: missing/duplicate/unknown keys",
        )
        numeric = idx.select_dtypes(include="number")
        check(np.isfinite(numeric.to_numpy()).all(), f"{name}: nonfinite values")
        normalized[name] = idx
    d, l, c, p, h = [normalized[name] for name in MONTHLY]
    for name, frame in [("deposits", d), ("loans", l), ("credit_cards", c)]:
        check(
            (frame[["opening_balance", "closing_balance", "average_balance"]] >= 0)
            .all()
            .all(),
            f"{name}: negative balance",
        )
        previous = frame.groupby(level=0).closing_balance.shift()
        mask = previous.notna()
        equals(
            frame.loc[mask, "opening_balance"], previous[mask], f"{name}: continuity"
        )
        equals(
            frame.average_balance,
            (frame.opening_balance + frame.closing_balance) / 2,
            f"{name}: average",
        )
    equals(
        d.closing_balance,
        d.opening_balance + d.inflows - d.outflows,
        "Deposit reconciliation",
    )
    equals(
        d.business_profit,
        d.business_revenue - d.business_expenses,
        "Business profit reconciliation",
    )
    check(
        (d[["inflows", "outflows", "owner_contribution", "owner_distribution"]] >= 0)
        .all()
        .all(),
        "Negative cash flow",
    )
    equals(
        l.closing_balance,
        l.opening_balance + l.drawdowns - l.principal_repayment,
        "Loan reconciliation",
    )
    equals(
        l.interest_revenue,
        (l.average_balance * l.interest_rate_annual / 12).round(2),
        "Loan interest",
    )
    equals(
        c.closing_balance,
        c.opening_balance
        + c.purchase_volume
        + c.interest_revenue
        + c.fee_revenue
        - c.payments,
        "Card reconciliation",
    )
    check((c.closing_balance <= c.credit_limit).all(), "Card limit exceeded")
    equals(
        c.interest_revenue,
        (c.interest_bearing_balance * c.interest_rate_annual / 12).round(2),
        "Card interest",
    )
    for flag, frame in [("has_loan", l), ("has_credit_card", c)]:
        check((frame[flag] == h[flag]).all(), f"{flag}: holdings mismatch")
        absent = ~h[flag]
        equals(
            frame.loc[absent, "closing_balance"], 0, f"{flag}: balance without holding"
        )
        equals(
            frame.loc[absent, "interest_revenue"], 0, f"{flag}: revenue without holding"
        )
        if flag == "has_loan":
            check(
                (frame.loc[h[flag], "closing_balance"] > 0).all(),
                "Active loan has zero balance",
            )
    equals(
        p.deposit_revenue,
        (d.average_balance * (0.04 - 0.012) / 12).round(2),
        "Deposit revenue",
    )
    equals(p.lending_revenue, l.interest_revenue, "Lending revenue link")
    equals(
        p.card_revenue,
        c.interest_revenue + c.interchange_revenue + c.fee_revenue,
        "Card revenue link",
    )
    equals(
        p.total_revenue,
        p.deposit_revenue + p.lending_revenue + p.card_revenue + p.service_fee_revenue,
        "Revenue total",
    )
    equals(
        p.allocated_expenses,
        p.servicing_expense
        + p.loan_funding_expense
        + p.card_funding_expense
        + p.credit_cost_expense,
        "Expense total",
    )
    equals(
        p.profitability, p.total_revenue - p.allocated_expenses, "Bank profitability"
    )

    def cents(values):
        return np.rint(np.asarray(values) * 100).astype(np.int64)

    check(
        np.array_equal(
            cents(p.profitability), cents(p.total_revenue) - cents(p.allocated_expenses)
        ),
        "Bank profitability: exact cent reconciliation",
    )
    for signal, holding, activity, threshold in [
        ("merchant_cross_sell", "has_merchant_services", d.business_revenue, 50000),
        ("payroll_cross_sell", "has_payroll_services", d.business_revenue, 80000),
        ("card_cross_sell", "has_credit_card", d.business_revenue, 25000),
        ("treasury_cross_sell", "has_treasury_services", d.closing_balance, 200000),
    ]:
        check(
            (h[signal] == (~h[holding] & (activity >= threshold))).all(),
            f"{signal}: rule mismatch",
        )

    flags = [col for col in h if col.startswith("has_")]
    equals(h.product_count, h[flags].sum(axis=1), "Product count")
    for signal, holding in [
        ("merchant_cross_sell", "has_merchant_services"),
        ("payroll_cross_sell", "has_payroll_services"),
        ("treasury_cross_sell", "has_treasury_services"),
        ("card_cross_sell", "has_credit_card"),
    ]:
        check(not (h[signal] & h[holding]).any(), f"{signal}: already held product")
    for _, frame in d.groupby(level=0):
        balances = frame.closing_balance.tolist()
        calculated = [
            sustained_decline(balances[: i + 1]) for i in range(len(balances))
        ]
        check(
            calculated == frame.attrition_indicator.tolist(), "Attrition rule mismatch"
        )
    correlation = float(d.business_revenue.corr(d.average_balance))
    check(correlation > 0.65, "Weak deposit/revenue relationship")
    return {
        "passed": True,
        "row_counts": {name: len(frame) for name, frame in tables.items()},
        "deposit_business_revenue_correlation": round(correlation, 6),
        "customers_with_attrition_indicator": int(
            d.reset_index().groupby("customer_id").attrition_indicator.any().sum()
        ),
        "currency": "USD",
        "synthetic_only": True,
    }
