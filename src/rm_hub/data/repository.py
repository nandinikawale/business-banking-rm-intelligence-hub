from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class Filters:
    rm_id: str | None = None
    industry: str | None = None
    region: str | None = None


def _where(filters, alias=""):
    prefix = f"{alias}." if alias else ""
    conditions, parameters = [], []
    for column in ("rm_id", "industry", "region"):
        value = getattr(filters or Filters(), column)
        if value is not None:
            conditions.append(f"{prefix}{column} = ?")
            parameters.append(value)
    return conditions, parameters


def month_date(value):
    parsed = pd.Timestamp(value)
    if (
        pd.isna(parsed)
        or parsed.day != 1
        or parsed.tzinfo is not None
        or parsed.time() != pd.Timestamp("2024-01-01").time()
    ):
        raise ValueError("Use a first-of-month date such as 2025-12-01")
    return parsed.date()


class Repository:
    def __init__(self, connection):
        self.connection = connection

    def periods(self) -> list[date]:
        return [
            row[0]
            for row in self.connection.execute(
                "SELECT DISTINCT month FROM deposits ORDER BY month"
            ).fetchall()
        ]

    def resolve_month(self, month=None):
        periods = self.periods()
        selected = periods[-1] if month is None else month_date(month)
        if selected not in periods:
            raise ValueError(f"No data for month {selected}")
        return selected

    def managers(self):
        return self.connection.execute(
            "SELECT * FROM relationship_managers ORDER BY rm_id"
        ).fetchdf()

    def customers(self, filters=None):
        conditions, parameters = _where(filters, "c")
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        return self.connection.execute(
            "SELECT c.*, r.rm_name FROM customers c JOIN relationship_managers r USING (rm_id)"
            + where
            + " ORDER BY c.customer_id",
            parameters,
        ).fetchdf()

    def profile(self, customer_id):
        result = self.connection.execute(
            "SELECT c.*, r.rm_name FROM customers c JOIN relationship_managers r USING (rm_id) WHERE c.customer_id = ?",
            [customer_id],
        ).fetchdf()
        if result.empty:
            raise LookupError(f"Unknown customer: {customer_id}")
        return result.iloc[0].to_dict()

    def history(self, filters=None, customer_id=None, start=None, end=None):
        conditions, parameters = _where(filters)
        for column, operator, value in [
            ("customer_id", "=", customer_id),
            ("month", ">=", start),
            ("month", "<=", end),
        ]:
            if value is not None:
                conditions.append(f"{column} {operator} ?")
                parameters.append(month_date(value) if column == "month" else value)
        if (
            start is not None
            and end is not None
            and month_date(start) > month_date(end)
        ):
            raise ValueError("Start month must not follow end month")
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        return self.connection.execute(
            "SELECT * FROM customer_monthly" + where + " ORDER BY customer_id, month",
            parameters,
        ).fetchdf()

    def snapshot(self, month=None, filters=None):
        selected = self.resolve_month(month)
        return self.history(filters=filters, start=selected, end=selected)
