# Changelog

## Unreleased

### Added on 10 November 2026

- Portfolio Overview explains deposit movement with increases, decreases, net change,
  the largest customer contributors and complete movement details. Remaining customers
  are included as a net residual so the contributions reconcile.
- Customer 360 includes a bank profitability waterfall, prior-month totals and
  revenue/cost changes with their impact on profit. Deposit interest is not deducted twice.
- RM Opportunities offers an app-filtered CSV worklist download with reporting month,
  customer/RM details, industry, region, supporting measures and explanations.
  Multiple signals per customer are preserved.
- Added reconciliation, missing-period, zero-baseline, filter, CSV quoting,
  Unicode and spreadsheet formula-text tests.
- Added feature definitions and actual screenshots of the additions.

### Updated

- Increased the shared BUSINESS BANKING label to 18 px semibold light text.
  Midnight navy colors and page navigation are retained.
- Updated architecture, setup and existing-repository upload instructions.
- The seven default CSVs, seed 42 and January 2024 to December 2025 are unchanged.
- Included the earlier reviewed PDF as a historical development report;
  excluded its unfinished local Word draft.

### Verification

- The pre-change baseline passed 51 tests; the enhanced suite passed 60.
- Lint and formatting checks passed.
- Browser checks verified all three features, the existing theme, desktop/mobile
  branding and mobile navigation.
- The December 2025 CSV contained 1,643 signals for 814 unique customers.
  A retention-only CSV contained 133 retention signals.
- SHA-256 checks confirmed all seven default CSVs were unchanged.

These are local results, not a claim about a remote GitHub Actions run.
Streamlit Community Cloud deployment is still pending.
