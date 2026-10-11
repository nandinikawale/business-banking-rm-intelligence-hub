import pytest

from banking_data.cli import generate
from banking_data.config import Config
from banking_data.export import write_outputs
from banking_data.validation import validate
from rm_hub.data.connection import analytics_connection
from rm_hub.data.repository import Repository


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    config = Config(customers=30)
    tables, scenarios = generate(config)
    root = tmp_path_factory.mktemp("analytics")
    write_outputs(
        tables,
        config,
        validate(tables, config),
        scenarios,
        root / "csv",
        root / "reports",
    )
    return root / "csv", tables


@pytest.fixture(scope="module")
def repository(dataset):
    with analytics_connection(dataset[0]) as connection:
        yield Repository(connection)
