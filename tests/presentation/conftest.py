from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from banking_data.cli import generate
from banking_data.config import Config
from banking_data.export import write_outputs
from banking_data.validation import validate
from rm_hub.settings import PROJECT_ROOT


@pytest.fixture(scope="module")
def ui_dataset(tmp_path_factory):
    root = tmp_path_factory.mktemp("presentation")
    config = Config(customers=30)
    tables, scenarios = generate(config)
    write_outputs(
        tables,
        config,
        validate(tables, config),
        scenarios,
        root / "csv",
        root / "reports",
    )
    return root / "csv", tables


@pytest.fixture
def app(monkeypatch, ui_dataset):
    monkeypatch.setenv("RM_HUB_DATA_DIR", str(ui_dataset[0]))
    return AppTest.from_file(
        str(Path(PROJECT_ROOT) / "streamlit_app" / "app.py"), default_timeout=90
    ).run()
