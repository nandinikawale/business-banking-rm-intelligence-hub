# Analytics architecture

Generation and analytics are separate packages. Production rm_hub modules never
import banking_data or simulation labels from the generation manifest.

## Flow

Seven synthetic CSVs -> typed DuckDB views -> Repository -> business services ->
Streamlit Portfolio Overview, Customer 360, and RM Opportunities.

- settings.py resolves paths from package location, independent of the terminal's
  working directory. Pass a data_dir for fixtures or another synthetic dataset.
- data/schemas.py defines exact CSV columns and types. Money uses DECIMAL(20,2),
  dates DATE, flags BOOLEAN, annual rates DOUBLE. Pandas results expose decimal
  money as floats; summaries are rounded to cents.
- data/connection.py opens a private in-memory connection, verifies headers,
  non-null values, unique keys, synthetic flags, foreign keys, first-of-month
  labels and aligned monthly coverage. It registers file-backed CSV views,
  not a persisted database. Use analytics_connection() to guarantee closure.
- data/repository.py returns DataFrames from parameterized SQL. The joined
  customer_monthly view joins every financial table on customer_id AND month.
  Filters combine RM, industry, and region using AND. IDs stay SQL parameters.
- services/portfolio.py calculates selected-month totals, product penetration,
  calendar month-over-month changes, monthly trends, and industry/RM/region
  concentration. First-month and zero-baseline percentage changes are None.
  Empty filters return zero counts/totals or empty result frames.
- services/customer.py provides profiles, financial histories through the selected
  month, snapshots, and additions/removals in product holdings.
- services/opportunities.py independently calculates documented demonstration
  signals from observed history and holdings. Retention comes first (priority 1),
  followed by cross-sell (priority 2), with stable RM/customer/product sorting.
  Priorities are a display convention, not a model score.

## Metric meanings

Deposit/loan/card balances are stocks for one month, never sums over time.
Revenue, allocated expenses, and bank profitability are monthly flows.
business_profit is fictional customer operating profit; profitability is bank
relationship profitability. Product penetration denominator is selected customers.

Retention requires four consecutive monthly observations, three decreases,
>=20% total decline, and starting deposits >=USD 10k. Cross-sell thresholds:
merchant sales >=50k, payroll >=80k, card >=25k, treasury deposits >=200k,
and the product must be absent. Reasons expose values and thresholds.
The selected month cuts off future history. CSV flags are used only as independent
test controls, not as the service's decision input. No generation labels are read.

The data contract contains all customers for every period; every monthly table
must have the same customer/month keys. Full financial generation checks remain
in banking_data.validation. Analytics startup checks structural integrity.

## Connection lifecycle

One connection belongs to one request/session, not a global shared connection.
CSV views read local files. Do not regenerate files during active queries; finish
the generator and reopen the connection to refresh data. Missing CSVs produce
instructions to generate them; analytics never downloads or generates data.

## Usage

```python
from rm_hub.data.connection import analytics_connection
from rm_hub.data.repository import Filters, Repository
from rm_hub.services.portfolio import portfolio_summary

with analytics_connection() as connection:
    repository = Repository(connection)
    summary = portfolio_summary(repository, "2025-12-01", Filters(rm_id="SYN-RM001"))
```

DuckDB references: [CSV import](https://duckdb.org/docs/current/data/csv/overview)
and [Python DB API](https://duckdb.org/docs/current/clients/python/dbapi).

## Streamlit presentation

- streamlit_app/app.py configures the shell, synthetic-data notice and navigation.
  All three requested pages use native top navigation via position="top"; filters stay in the sidebar.
- streamlit_app/views/portfolio_overview.py composes filters, eight metric cards,
  balance/economics trends, industry/RM concentration, product penetration, and
  expandable concentration/customer tables. It delegates all calculations to
  rm_hub services; there is no SQL or generation logic in the page.
- streamlit_app/components.py owns display formatting and reusable Plotly charts.
- streamlit_app/data.py caches returned data, not DuckDB connections. Cache keys
  include directory, filters/month, and the filename/size/mtime_ns tuple of all
  seven CSVs. Each cache miss owns and closes one short-lived connection.
  Regeneration normally changes timestamps and refreshes the next rerun. If a
  file is replaced with identical timestamps and sizes, clear Streamlit's cache.
  Do not regenerate files while active queries are running.
- .streamlit/config.toml sets the light theme and disables usage telemetry.
- Set RM_HUB_DATA_DIR to use another synthetic data directory. Tests use this
  override with temporary fixtures; the default stays project-relative.

All customers and all periods remain fictional. Money cards abbreviate USD values
for readability; tooltips and data tables show exact amounts. Product penetration
is calculated over the selected customer population. Empty selections have a clear
message. First-month comparisons and zero-baseline percentage changes have no
displayed delta.

Streamlit tests verify initial loading, RM filtering, incompatible filters,
historical cutoffs, first-month deltas, missing CSVs, and fingerprint invalidation.

References: [navigation](https://docs.streamlit.io/develop/api-reference/navigation/st.navigation),
[data caching](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data),
and [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).

## Customer 360 presentation

Customer 360 is a file-based page registered at /customer-360. The common app shell
retains navigation and the synthetic-data notice. Its selectors have independent
customer_id and customer_month keys to avoid conflicts with portfolio filters.

The cached load_customer adapter calls customer_360 and opportunities with a
customer_id restriction. The latter restriction is applied in Repository.history
as a SQL parameter. It avoids scanning other customers' histories in Python and
uses the same opportunity rules as portfolio-level signals. No generator labels
or future observations enter the page.

Cached results are keyed by data directory, all seven file fingerprints, customer,
and reporting month. Connections close after each cache miss. Reusable labels,
metric cards, and Plotly charts remain in components.py.

The page includes the profile, eight bank/product metrics, balance and bank
economics charts, holdings, product changes, review signals, and expandable
business operating metrics/chart and detailed history. Business age is labeled
as the value at January 2024. Product changes describe movements after the first
observed month; opening holdings are not presented as new adoptions.

Tests execute the registered page from the main app using AppTest.switch_page,
verify selected-customer financial values, exclude future months/product adoptions,
check zero balances for nonholders and first-month rule limitations, and handle
missing CSVs. Analytics tests compare customer-scoped signals with the portfolio
signal subset.

## RM Opportunities presentation

RM Opportunities is the file-based page at /rm-opportunities. It has independent
opp_month, opp_rm, opp_industry, opp_region, opp_type and opp_product widget keys.

load_opportunities caches the backend signal DataFrame keyed by data directory,
all CSV fingerprints, reporting month and population filters. A connection opens
and closes on cache misses. Signal/product filtering, distinct-customer summary
counts, and grouped distributions live in reusable services, not SQL in the page.

The new filter_opportunities, opportunity_summary and opportunity_breakdown helpers
retain deterministic priority/RM/customer/product order, count signals separately
from customers, and aggregate signal counts by RM identity/type and product/type.
All cards, charts and table rows share the resulting selected worklist.
The chart uses existing Plotly styling and documented display labels.

Default priority 1 is retention; priority 2 is cross-sell. No ranking model,
estimated revenue uplift, or inferred probability is introduced. The worklist
formats retention thresholds as percent decline and other thresholds as USD.
Deposit change percentages are already percentage-point values (e.g. -29.5),
so the display does not multiply them by 100.

Tests independently verify unique-customer vs signal counts with a small fixture,
grouped count reconciliation, review ordering, population/type/product filters,
CSV-indicator agreement, January 2024 cutoffs and missing/empty data handling.
GitHub CI's existing full pytest command includes these tests.


On narrow screens, native Streamlit navigation falls back to its collapsible menu. Expand the sidebar/menu with the top-left chevron to choose a page and access filters.
