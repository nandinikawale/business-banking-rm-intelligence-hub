# Contributing

Start with the setup and generation instructions in README.md. Use Python 3.13
and the committed uv.lock; do not change the lockfile merely to run the project.

## Development workflow

```sh
python -m uv sync --locked --group app
python -m uv run --locked --group app ruff format .
python -m uv run --locked --group app ruff check .
python -m uv run --locked --group app pytest
```

Keep data generation in banking_data, analytics and business calculations in
rm_hub, and presentation in streamlit_app. Add meaningful tests for changed
calculations, rules, joins, or user interactions. Use temporary synthetic fixtures.

Do not add real customer data, real account/tax identifiers, internal banking
datasets, public economic datasets, or confidential rules. Document changes to
fictional simulation assumptions and data schemas. Do not commit virtual
environments, generated outputs, agent-skill links, or credentials.

Maintain fixed January 2024–December 2025 dates and seed 42 for the default demo.
App code must not use generation-only scenario assignments or observations after
the selected reporting month.

For a proposed change, describe the problem, resulting behavior, and validation.
The project uses the [MIT License](LICENSE). Contribution acceptance is managed by the repository owner.
