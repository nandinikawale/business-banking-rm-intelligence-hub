# Fictional simulation assumptions

All parameters are invented for demonstration, without downloaded data or calibration.

- Business annual sales are bounded, skewed lognormal draws. Deposit liquidity scales
  with sales. Industry margins, seasonal amplitude, and seasonal peaks differ.
- Stable (40%), growth (25%), seasonal (15%), attrition (12%), and distressed (8%)
  scenarios are sampled. Monthly shocks persist with coefficient 0.65.
  Scenario labels are generation-only diagnostics.
- Deposit closing balances respond gradually to sales and liquidity needs.
  Attrition cases lose 11% of remaining deposits monthly from April 2025.
  Distress cases have declining sales, reduced margins, and liquidity erosion.
- Profiles and sales are fictional business values, not bank income.
  Deposits expose monthly business revenue, operating expenses, and operating profit.
- Cash movements reconcile through business sales, non-card operating expenses,
  loan drawdowns/repayments, card payments, service fees, deposit interest, and
  explicit owner contributions/distributions. Owner transfers are balancing
  liquidity-policy movements, not a claim of a fully modeled business balance sheet.
- Loan balances amortize and may draw again in April 2024 and April 2025.
  Customer loan rates are fixed fictional 6.5–9.5% annual rates.
- Cards revolve a fraction of purchase volume, with higher utilization in distress.
  Card interest is charged on opening outstanding balances at 19% annual;
  interchange is 1.5% of purchases, and monthly fees are USD 5 for holders.
  No daily balances or grace periods are modeled.
- Monthly averages are opening/closing midpoints, not daily averages.
- Deposit bank revenue is net interest spread: average deposits * (4% - 1.2%) / 12.
  Deposit interest expense is disclosed separately and already netted in deposit
  revenue; it is not deducted again in allocated expenses.
- Loan/card funding costs are 3% annually; credit cost allocations are 0.6% for
  loans and 1.8% for cards. Servicing uses fixed and activity-driven costs.
  Bank profitability = total bank revenue - allocated expenses.
- Product adoption depends on business industry/size. Growth customers adopt payroll
  in January 2025. Loan/card flags exactly match financial records.
- Cross-sell flags require missing products and fictional activity thresholds:
  merchant monthly sales >=50k; payroll >=80k; card >=25k; treasury deposits >=200k.
  These are demonstration indicators, not suitability or credit decisions.
- Attrition indicator requires three consecutive balance declines, at least 20%
  cumulative decline, and starting balance >=10k. Four observations are required.
  It may flag distressed or seasonal businesses and does not prove actual attrition.
