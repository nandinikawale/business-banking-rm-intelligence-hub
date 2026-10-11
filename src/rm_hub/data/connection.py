import csv
from contextlib import contextmanager
from pathlib import Path

import duckdb

from rm_hub.data.schemas import SCHEMAS
from rm_hub.settings import Settings


class DataValidationError(ValueError):
    """CSV contract prevents reliable analytics."""


def _validate(connection):
    for name in SCHEMAS:
        keys = "rm_id" if name == "relationship_managers" else "customer_id"
        if name not in ("customers", "relationship_managers"):
            keys += ", month"
        if connection.execute(
            f"SELECT count(*) FROM (SELECT {keys}, count(*) n FROM {name} GROUP BY {keys} HAVING count(*) > 1)"
        ).fetchone()[0]:
            raise DataValidationError(f"{name}: duplicate keys")
        null_condition = " OR ".join(f"{column} IS NULL" for column in SCHEMAS[name])
        if connection.execute(
            f"SELECT count(*) FROM {name} WHERE {null_condition}"
        ).fetchone()[0]:
            raise DataValidationError(f"{name}: missing values")
    if connection.execute(
        "SELECT count(*) FROM customers WHERE NOT is_synthetic"
    ).fetchone()[0]:
        raise DataValidationError("Only explicitly synthetic records are supported")
    if connection.execute(
        "SELECT count(*) FROM customers c LEFT JOIN relationship_managers r USING (rm_id) WHERE r.rm_id IS NULL"
    ).fetchone()[0]:
        raise DataValidationError("Unknown RM")
    for name in ("deposits", "loans", "credit_cards", "profitability", "products"):
        if connection.execute(
            f"SELECT count(*) FROM {name} d LEFT JOIN customers c USING (customer_id) WHERE c.customer_id IS NULL"
        ).fetchone()[0]:
            raise DataValidationError(f"{name}: unknown customer")
        if connection.execute(
            f"SELECT count(*) FROM {name} WHERE day(month) != 1"
        ).fetchone()[0]:
            raise DataValidationError(f"{name}: month must be first of month")
        for left, right in [(name, "deposits"), ("deposits", name)]:
            if connection.execute(
                f"SELECT count(*) FROM (SELECT customer_id, month FROM {left} EXCEPT SELECT customer_id, month FROM {right})"
            ).fetchone()[0]:
                raise DataValidationError(
                    f"{name}: inconsistent customer/month coverage"
                )
    expected_coverage = connection.execute("""
        SELECT count(*) FROM (
            SELECT c.customer_id, m.month
            FROM customers c CROSS JOIN (SELECT DISTINCT month FROM deposits) m
            EXCEPT SELECT customer_id, month FROM deposits
        )
    """).fetchone()[0]
    if expected_coverage:
        raise DataValidationError("Deposits: missing customer/month coverage")

    if not connection.execute("SELECT count(*) FROM deposits").fetchone()[0]:
        raise DataValidationError("No monthly data found")


def open_connection(data_dir=None):
    """Own one connection per request/session; reopen after regenerating files."""
    directory = Path(
        data_dir if data_dir is not None else Settings().data_dir
    ).resolve()
    missing = [
        f"{name}.csv" for name in SCHEMAS if not (directory / f"{name}.csv").is_file()
    ]
    if missing:
        raise FileNotFoundError(
            f"Missing CSVs in {directory}: {', '.join(missing)}. "
            "From the project root run: python -m uv run banking-data generate"
        )
    connection = duckdb.connect(":memory:")
    try:
        for name, schema in SCHEMAS.items():
            path = directory / f"{name}.csv"
            with path.open(encoding="utf-8", newline="") as handle:
                if next(csv.reader(handle), []) != list(schema):
                    raise DataValidationError(
                        f"{name}: unexpected columns or column order"
                    )
            connection.read_csv(
                str(path), columns=schema, header=True, auto_detect=False
            ).create_view(name)
        _validate(connection)
        connection.execute("""
            CREATE VIEW customer_monthly AS
            SELECT c.*, r.rm_name, d.month,
                d.opening_balance AS deposit_opening_balance,
                d.closing_balance AS deposit_balance,
                d.average_balance AS average_deposit_balance,
                d.business_revenue, d.business_expenses, d.business_profit,
                d.transaction_count, d.attrition_indicator,
                l.closing_balance AS loan_balance,
                a.closing_balance AS card_balance, a.credit_limit,
                a.purchase_volume, a.interest_revenue AS card_interest_revenue,
                p.* EXCLUDE (customer_id, month),
                h.* EXCLUDE (customer_id, month)
            FROM deposits d
            JOIN customers c USING (customer_id)
            JOIN relationship_managers r USING (rm_id)
            JOIN loans l ON d.customer_id = l.customer_id AND d.month = l.month
            JOIN credit_cards a ON d.customer_id = a.customer_id AND d.month = a.month
            JOIN profitability p ON d.customer_id = p.customer_id AND d.month = p.month
            JOIN products h ON d.customer_id = h.customer_id AND d.month = h.month
        """)
        return connection
    except Exception:
        connection.close()
        raise


@contextmanager
def analytics_connection(data_dir=None):
    connection = open_connection(data_dir)
    try:
        yield connection
    finally:
        connection.close()
