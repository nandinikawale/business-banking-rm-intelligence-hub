# Business analytics enhancements

## Actual application screenshots

- [Portfolio deposit movements](images/portfolio-overview-insights.png)
- [Customer profitability breakdown](images/customer-360-profitability.png)
- [Opportunity worklist export](images/rm-opportunities-export.png)

## Deposit movement analysis

Portfolio Overview compares the selected month's closing deposits with the preceding
calendar month for the same customers and the same RM, industry and region filters.
Each customer's dollar change is current closing balance minus prior closing balance.
Percentage change is dollar change divided by prior balance, times 100; a zero prior
balance produces an unavailable percentage rather than infinity.

The section reports positive movements, negative movements and their net. The chart
shows up to five increases and five decreases, plus **Other customers (net)** for all
remaining customers. That residual can include offsetting increases and decreases.
Every customer is represented exactly once; chart contributions reconcile to the
net portfolio change. Hover identifies each fictional business and the number of
customers represented. The expandable table includes every filtered customer,
prior/current balance, dollar change, percentage change, RM, industry and region.

January 2024 has no prior-month comparison. Missing comparison periods are not treated
as zero. A mismatched customer population raises a validation error instead of silently
dropping customers. An empty portfolio uses the page's existing empty-selection state.

## Bank relationship profitability

Customer 360 adds a waterfall below the existing balance and economics trends:

- Deposit revenue, already net of deposit interest expense.
- Lending revenue.
- Card revenue.
- Service revenue.
- Allocated expenses, deducted once.
- Resulting bank relationship profitability.

Revenue components reconcile to total bank revenue; servicing, loan funding,
card funding and credit cost allocations reconcile to allocated expenses.
Bank revenue minus allocated expenses reconciles to profitability.
These are fictional allocations, not customer operating income or production bank pricing.

The totals table compares the selected month with the preceding calendar month.
The expandable component table shows revenue/cost amounts, their changes, and their
impact on profit. Cost amounts are positive expenses; a cost increase has a negative
profit impact. Total rows are separate from component rows to avoid double counting.
When no preceding calendar month exists, the current breakdown remains available
and the comparison is explicitly unavailable. Future observations are not used.

## Opportunity worklist export

The dedicated download on RM Opportunities serializes the same formatted worklist
used by its table after the app's population, signal-type and product filters.
The download includes the reporting month, customer ID, fictional business, RM,
industry, region, signal, potential product, activity, labeled rule threshold,
deposit change percentage where applicable, review order and supporting observation.

The filename uses the selected month, for example rm_opportunities_2025-12.csv.
A customer with multiple signals retains multiple rows. Table-only interactive
sorting does not change the CSV's default retention-first order. Empty selections
show the existing explanatory message and do not offer a misleading download.

CSV output uses ordinary CSV quoting, two decimal places for numeric fields and
UTF-8 with a BOM for Excel compatibility. Formula-like text beginning with =, +,
- or @ after leading whitespace receives a leading apostrophe. Numeric negative
values remain numbers; display data is not mutated. No files are written on the
server when a user downloads a worklist.

## Implementation boundaries

- src/rm_hub/services/relationship_insights.py owns movement and profitability logic.
- streamlit_app/data.py loads and caches the new bundles alongside existing views.
- streamlit_app/insights.py renders charts and supporting tables.
- streamlit_app/exports.py owns shared worklist formatting and CSV serialization.

No new datasets, generation parameters, prediction models, AI services or cloud
dependencies are introduced. The existing midnight navy theme remains in place. The shared BUSINESS BANKING
sidebar label is 18 px semibold light text, verified on desktop and mobile.

## Validation

Tests compare movement and profitability results with independent source CSV totals,
exercise filters, zero baselines, offsetting movements, missing comparison periods,
and component reconciliation. Export tests cover filter context, Unicode, commas,
newlines, empty headers and formula-like text. Presentation regressions cover all
three pages and the empty download state. Browser checks exercise actual downloads.

Return to the [project README](../README.md).
