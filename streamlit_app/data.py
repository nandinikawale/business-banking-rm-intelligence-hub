import os
from pathlib import Path

import streamlit as st

from rm_hub.data.connection import analytics_connection
from rm_hub.data.repository import Filters, Repository
from rm_hub.data.schemas import SCHEMAS
from rm_hub.services.customer import customer_360
from rm_hub.services.opportunities import opportunities
from rm_hub.services.portfolio import concentration, portfolio_summary, portfolio_trends
from rm_hub.settings import Settings


def data_directory():
    return (
        Path(os.environ.get("RM_HUB_DATA_DIR", Settings().data_dir))
        .expanduser()
        .resolve()
    )


def fingerprint(directory):
    """All files participate; timestamps and sizes invalidate cached results."""
    directory = Path(directory)
    missing = [
        f"{name}.csv" for name in SCHEMAS if not (directory / f"{name}.csv").is_file()
    ]
    if missing:
        raise FileNotFoundError("Missing synthetic data files: " + ", ".join(missing))
    return tuple(
        (
            name,
            (directory / f"{name}.csv").stat().st_size,
            (directory / f"{name}.csv").stat().st_mtime_ns,
        )
        for name in SCHEMAS
    )


@st.cache_data(show_spinner=False, max_entries=8)
def load_options(directory, file_fingerprint):
    with analytics_connection(directory) as connection:
        repository = Repository(connection)
        return {
            "periods": repository.periods(),
            "customers": repository.customers(),
            "managers": repository.managers(),
        }


@st.cache_data(show_spinner=False, max_entries=64)
def load_portfolio(directory, file_fingerprint, month, rm_id, industry, region):
    filters = Filters(rm_id=rm_id, industry=industry, region=region)
    with analytics_connection(directory) as connection:
        repository = Repository(connection)
        return {
            "summary": portfolio_summary(repository, month, filters),
            "trends": portfolio_trends(repository, filters, end=month),
            "industry": concentration(repository, month, filters, group_by="industry"),
            "rm": concentration(repository, month, filters, group_by="rm_id"),
            "snapshot": repository.snapshot(month, filters),
        }


@st.cache_data(show_spinner=False, max_entries=128)
def load_customer(directory, file_fingerprint, customer_id, month):
    with analytics_connection(directory) as connection:
        repository = Repository(connection)
        bundle = customer_360(repository, customer_id, month)
        bundle["signals"] = opportunities(repository, month, customer_id=customer_id)
        return bundle


@st.cache_data(show_spinner=False, max_entries=64)
def load_opportunities(directory, file_fingerprint, month, rm_id, industry, region):
    filters = Filters(rm_id=rm_id, industry=industry, region=region)
    with analytics_connection(directory) as connection:
        return opportunities(Repository(connection), month, filters)
