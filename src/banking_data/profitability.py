def money(value):
    return round(float(value), 2)


def calculate_profitability(
    deposit_average, loan_average, card, holdings, transactions
):
    # All rates below are fictional demonstration parameters.
    deposit_interest = money(deposit_average * 0.012 / 12)
    deposit_revenue = money(deposit_average * (0.04 - 0.012) / 12)
    lending_revenue = card["loan_interest_revenue"]
    card_revenue = money(
        card["interest_revenue"] + card["interchange_revenue"] + card["fee_revenue"]
    )
    service_fees = money(
        25
        + 60 * holdings["has_payroll_services"]
        + 120 * holdings["has_treasury_services"]
        + 0.25 * transactions * holdings["has_merchant_services"]
    )
    servicing = money(
        75
        + transactions * 0.12
        + 30 * holdings["has_loan"]
        + 15 * holdings["has_credit_card"]
    )
    loan_funding = money(loan_average * 0.03 / 12)
    card_funding = money(card["average_balance"] * 0.03 / 12)
    credit_cost = money(
        loan_average * 0.006 / 12 + card["average_balance"] * 0.018 / 12
    )
    expenses = money(servicing + loan_funding + card_funding + credit_cost)
    revenue = money(deposit_revenue + lending_revenue + card_revenue + service_fees)
    return {
        "deposit_interest_expense": deposit_interest,
        "deposit_revenue": deposit_revenue,
        "lending_revenue": lending_revenue,
        "card_revenue": card_revenue,
        "service_fee_revenue": service_fees,
        "total_revenue": revenue,
        "servicing_expense": servicing,
        "loan_funding_expense": loan_funding,
        "card_funding_expense": card_funding,
        "credit_cost_expense": credit_cost,
        "allocated_expenses": expenses,
        "profitability": money(revenue - expenses),
    }
