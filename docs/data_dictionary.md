# CSV contract

All records are synthetic. Currency: USD. Dates: ISO YYYY-MM-DD, first of month.
Annual rates are decimal fractions. Monetary values are rounded to cents.
All monthly tables have unique (customer_id, month) keys covering Jan 2024–Dec 2025.
Every customer_id references customers.csv; every rm_id references relationship_managers.csv.
Nonholders retain monthly rows with zero product balances and income.

| File | Grain | Contents |
|---|---|---|
| customers.csv | Customer | SYN-C identifier, fictional name, industry, size, age, fictional region, RM, relationship start, baseline annual business revenue, synthetic flag |
| relationship_managers.csv | RM | SYN-RM identifier, fictional numbered display name, fictional region |
| deposits.csv | Customer/month | Opening/closing/midpoint balances, total cash inflows/outflows, deposit rate, business sales/expenses/profit, owner cash contributions/distributions, transactions, attrition indicator |
| loans.csv | Customer/month | Holding flag, opening/closing/midpoint balances, drawdowns, principal repayments, annual interest rate, bank interest revenue |
| credit_cards.csv | Customer/month | Holding flag, limit, opening/closing/midpoint balances, purchase volume, payments, interest-bearing balance, annual rate, interest/interchange/fee revenues |
| profitability.csv | Customer/month | Deposit interest expense (disclosure), deposit/lending/card/service revenue, total revenue, servicing/loan funding/card funding/credit cost expenses, allocated expenses, bank profitability |
| products.csv | Customer/month | Six holding flags, total held products, four cross-sell flags |

## Field conventions

customer_id and rm_id are generated keys, not banking identifiers.
business_age_years is age at the beginning of the simulation.
baseline_annual_business_revenue is the initial sales scale, not realized yearly totals.
business_profit is operating profit before finance charges.
opening_balance and closing_balance are period stocks; do not sum them across months.
average_balance is the arithmetic midpoint of opening and closing balances.
Revenue, expenses, purchase volumes, transfers, and payments are monthly flows.
interest_bearing_balance is the opening card balance used to calculate interest.
product_count counts only has_* fields; cross-sell flags do not count as holdings.
attrition_indicator is a boolean rolling rule, not a probability or closure status.

See simulation_assumptions.md for each revenue equation, allocation, threshold,
timing assumption, and model limitation.
