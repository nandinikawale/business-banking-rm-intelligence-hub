import math

import pandas as pd

from .customers import INDUSTRIES
from .indicators import cross_sell, sustained_decline
from .profitability import calculate_profitability, money


def simulate(customers, config, rng):
    tables = {
        name: []
        for name in ("deposits", "loans", "credit_cards", "profitability", "products")
    }
    scenarios = {}
    months = pd.date_range(config.start, config.end, freq="MS")
    for customer in customers.itertuples(index=False):
        base = customer.baseline_annual_business_revenue / 12
        margin, amplitude, peak = INDUSTRIES[customer.industry]
        scenario = str(
            rng.choice(
                ["stable", "growth", "seasonal", "attrition", "distressed"],
                p=[0.40, 0.25, 0.15, 0.12, 0.08],
            )
        )
        scenarios[customer.customer_id] = scenario
        growth = {
            "stable": 0.001,
            "growth": 0.009,
            "seasonal": 0.001,
            "attrition": 0.001,
            "distressed": -0.002,
        }[scenario]
        holdings = {
            "has_deposit_account": True,
            "has_loan": bool(rng.random() < 0.55),
            "has_credit_card": bool(rng.random() < 0.62),
            "has_merchant_services": bool(
                rng.random()
                < (0.65 if customer.industry in ["Retail", "Hospitality"] else 0.25)
            ),
            "has_payroll_services": bool(rng.random() < 0.40),
            "has_treasury_services": bool(
                rng.random() < (0.55 if base > 400000 else 0.10)
            ),
        }
        liquidity_months = float(rng.uniform(0.8, 2.5))
        deposit = money(base * liquidity_months)
        loan = money(base * rng.uniform(1, 4)) if holdings["has_loan"] else 0.0
        card_balance = money(base * 0.025) if holdings["has_credit_card"] else 0.0
        limit = money(base * 0.35) if holdings["has_credit_card"] else 0.0
        loan_rate = round(float(rng.uniform(0.065, 0.095)), 6)
        shock = 0.0
        history = []
        for t, month in enumerate(months):
            key = {
                "customer_id": customer.customer_id,
                "month": month.strftime("%Y-%m-%d"),
            }
            shock = 0.65 * shock + float(rng.normal(0, 0.012))
            seasonal = 1 + amplitude * math.cos(2 * math.pi * (month.month - peak) / 12)
            sales = money(base * (1 + growth) ** t * seasonal * math.exp(shock))
            if scenario == "distressed" and t >= 12:
                sales = money(sales * 0.96 ** (t - 11))
            operating_margin = margin - (
                0.06 if scenario == "distressed" and t >= 12 else 0
            )
            business_expenses = money(sales * (1 - operating_margin))
            business_profit = money(sales - business_expenses)
            # Product adoption is persistent; all files use this same month's holdings.
            if scenario == "growth" and t == 12:
                holdings["has_payroll_services"] = True
            opening_loan = loan
            draws = money(base * 0.04) if holdings["has_loan"] and t in [3, 15] else 0.0
            principal = (
                money(min(opening_loan + draws, base * 0.025))
                if holdings["has_loan"]
                else 0.0
            )
            loan = money(opening_loan + draws - principal)
            loan_average = money((opening_loan + loan) / 2)
            loan_interest = money(loan_average * loan_rate / 12)
            tables["loans"].append(
                {
                    **key,
                    "has_loan": holdings["has_loan"],
                    "opening_balance": opening_loan,
                    "drawdowns": draws,
                    "principal_repayment": principal,
                    "closing_balance": loan,
                    "average_balance": loan_average,
                    "interest_rate_annual": loan_rate if holdings["has_loan"] else 0,
                    "interest_revenue": loan_interest,
                }
            )
            opening_card = card_balance
            purchases = money(sales * 0.08) if holdings["has_credit_card"] else 0.0
            card_interest = money(opening_card * 0.19 / 12)
            fee = 5.0 if holdings["has_credit_card"] else 0.0
            target_card = money(
                min(
                    limit * 0.60,
                    purchases * (0.75 if scenario == "distressed" else 0.30),
                )
            )
            payment = money(
                max(0, opening_card + purchases + card_interest + fee - target_card)
            )
            card_balance = money(
                opening_card + purchases + card_interest + fee - payment
            )
            card = {
                **key,
                "has_credit_card": holdings["has_credit_card"],
                "credit_limit": limit,
                "opening_balance": opening_card,
                "purchase_volume": purchases,
                "payments": payment,
                "closing_balance": card_balance,
                "average_balance": money((opening_card + card_balance) / 2),
                "interest_bearing_balance": opening_card,
                "interest_rate_annual": 0.19 if holdings["has_credit_card"] else 0,
                "interest_revenue": card_interest,
                "interchange_revenue": money(purchases * 0.015),
                "fee_revenue": fee,
            }
            tables["credit_cards"].append(card)
            opening_deposit = deposit
            target_deposit = money(sales * liquidity_months)
            if scenario == "attrition" and t >= 15:
                deposit = money(opening_deposit * 0.89)
            else:
                deterioration = 0.97 if scenario == "distressed" and t >= 12 else 1
                deposit = money(
                    max(
                        0,
                        (opening_deposit * 0.75 + target_deposit * 0.25)
                        * deterioration,
                    )
                )
            deposit_average = money((opening_deposit + deposit) / 2)
            transactions = max(
                1,
                int(
                    sales
                    / 500
                    * (0.89 ** max(0, t - 14) if scenario == "attrition" else 1)
                ),
            )
            profitability = calculate_profitability(
                deposit_average,
                loan_average,
                {**card, "loan_interest_revenue": loan_interest},
                holdings,
                transactions,
            )
            # Card purchases are included in operating expenses; subtract them from cash costs.
            core_inflows = money(
                sales + draws + profitability["deposit_interest_expense"]
            )
            core_outflows = money(
                business_expenses
                - purchases
                + principal
                + loan_interest
                + payment
                + profitability["service_fee_revenue"]
            )
            transfer = money(deposit - (opening_deposit + core_inflows - core_outflows))
            owner_contribution = max(0.0, transfer)
            owner_distribution = max(0.0, -transfer)
            inflows = money(core_inflows + owner_contribution)
            outflows = money(core_outflows + owner_distribution)
            history.append(deposit)
            tables["deposits"].append(
                {
                    **key,
                    "opening_balance": opening_deposit,
                    "inflows": inflows,
                    "outflows": outflows,
                    "closing_balance": deposit,
                    "average_balance": deposit_average,
                    "deposit_rate_annual": 0.012,
                    "business_revenue": sales,
                    "business_expenses": business_expenses,
                    "business_profit": business_profit,
                    "owner_contribution": owner_contribution,
                    "owner_distribution": owner_distribution,
                    "transaction_count": transactions,
                    "attrition_indicator": sustained_decline(history),
                }
            )
            tables["profitability"].append({**key, **profitability})
            tables["products"].append(
                {
                    **key,
                    **holdings,
                    "product_count": sum(holdings.values()),
                    **cross_sell(holdings, sales, deposit),
                }
            )
    return {name: pd.DataFrame(rows) for name, rows in tables.items()}, scenarios
