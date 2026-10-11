# Synthetic data generation

This directory holds **entirely fictional** banking datasets. No real customer
records, customer identifiers, public economic observations, external datasets,
or confidential business rules are used.

A GitHub clone includes the seven default synthetic CSVs under synthetic/.
**Generation is optional:** install dependencies and launch the app using the
[root README](../README.md). Follow the steps below to regenerate the data.
Alternative datasets and generated reports remain ignored.

## Optional regeneration after cloning

Open a terminal in the project root, the directory containing pyproject.toml,
not inside data/.

For generation only, Python 3.13 and these commands are sufficient:

```sh
python -m pip install uv==0.12.24
python -m uv sync --locked
python -m uv run --locked banking-data generate
python -m uv run --locked banking-data validate
```

The default generator does not require Streamlit, DuckDB, or Plotly. To also run
the dashboard, install the app group and launch from the same project root:

```sh
python -m uv sync --locked --group app
python -m uv run --locked --group app streamlit run streamlit_app/app.py
```

If Python is named python3.13 on macOS/Linux, substitute that command.
If VS Code on Windows selects .venv Python and cannot find uv, use py -3.13
instead of python, or invoke your main Python executable. uv manages the project
environment; activating it manually is unnecessary.

## Defaults and output files

Defaults: **1,000 customers**, **20 RMs**, **24 months from January 2024 through
December 2025**, **seed 42**, **USD**.

| File under synthetic/ | Grain | Default rows | Description |
| --- | --- | ---: | --- |
| customers.csv | Customer | 1,000 | Fictional business profile, synthetic customer ID, RM assignment |
| relationship_managers.csv | RM | 20 | Fictional numbered RM and region |
| deposits.csv | Customer/month | 24,000 | Deposits, cash flows, business operating results, attrition indicator |
| loans.csv | Customer/month | 24,000 | Holdings, balances, draws, repayments, interest revenue |
| credit_cards.csv | Customer/month | 24,000 | Holdings, limits, purchases, payments, balances, bank revenues |
| profitability.csv | Customer/month | 24,000 | Bank revenues, allocated costs, relationship profitability |
| products.csv | Customer/month | 24,000 | Product flags, product count, demonstration cross-sell flags |

Identifiers are generated locally, such as SYN-C000001 and SYN-RM001. Monthly
rows join on customer_id AND month; profiles join on customer_id and rm_id.
Nonholders retain monthly rows with zero loan/card balances and product income.

The generator also writes:

- ../reports/generation_manifest.json: parameters, hashes, and synthetic
  scenario assignments for diagnostics.
- ../reports/validation_report.json: row counts, integrity results,
  correlation diagnostic, and deposit-decline indicator counts.

These report paths are relative to this data/ directory; commands executed from
the project root write to reports/. The application does not use scenario labels
as predictions or decision inputs.

## Regenerate later

Stop Streamlit and close CSVs in Excel first. From the project root:

```sh
python -m uv run --locked banking-data generate
python -m uv run --locked banking-data validate
```

Generation overwrites the seven CSVs and two reports in their output directories.
It does not use the current date. Validation reads the CSVs and prints its results;
it does not regenerate the files. Restart the dashboard afterward to refresh
connections and cached results.

Stable inputs, seeded NumPy/Faker generators, deterministic ordering, CSV
formatting, and locked dependencies support reproduction. Compare manifest hashes
to confirm byte equality; platform/Python-patch differences can affect numerical
rounding, so cross-platform equality is not guaranteed.

## Explicit settings and custom datasets

The default parameters can be stated explicitly:

```sh
python -m uv run --locked banking-data generate --customers 1000 --seed 42 --output data/synthetic --reports reports
python -m uv run --locked banking-data validate --customers 1000 --output data/synthetic
```

Customer count and seed are configurable. **The CLI dates remain fixed**;
it does not accept --start or --months options.

For an alternative dataset without replacing the default files:

```sh
python -m uv run --locked banking-data generate --customers 5000 --seed 42 --output data/alternate --reports reports/alternate
python -m uv run --locked banking-data validate --customers 5000 --output data/alternate
```

Pass the same customer count to validation; it defaults to 1,000.
RM count remains 20. To view alternate CSVs, point the app at their directory
before launching.

PowerShell:

```powershell
$env:RM_HUB_DATA_DIR = (Resolve-Path 'data/alternate').Path
python -m uv run --locked --group app streamlit run streamlit_app/app.py
```

macOS/Linux:

```sh
export RM_HUB_DATA_DIR="$PWD/data/alternate"
python -m uv run --locked --group app streamlit run streamlit_app/app.py
```

Unset RM_HUB_DATA_DIR or open a fresh terminal to return to the default location.
Generated CSVs anywhere under data/ and report JSONs under reports/ are ignored
by Git. Directory placeholders remain tracked.

## Checks and limitations

Validation checks customer/RM keys, full monthly coverage, balance continuity,
deposit/loan/card equations, holding consistency, revenue links, bank profitability,
product counts, cross-sell rules, and the observed deposit-decline indicator.

Run generator tests independently:

```sh
python -m uv run --locked pytest tests/generation
```

See [CSV definitions](../docs/data_dictionary.md) for fields and units and
[simulation assumptions](../docs/simulation_assumptions.md) for equations and fictional parameters.
These are educational simulations, not calibrated banking models.
