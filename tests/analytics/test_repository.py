import pandas as pd
import pytest

from rm_hub.data.connection import DataValidationError, analytics_connection
from rm_hub.data.repository import Filters
from rm_hub.settings import PROJECT_ROOT, Settings


def test_monthly_join_and_types(repository, dataset):
    history = repository.history()
    assert len(history) == 30 * 24
    assert not history.duplicated(["customer_id", "month"]).any()
    expected = (
        dataset[1]["deposits"]
        .set_index(["customer_id", "month"])
        .closing_balance.sort_index()
    )
    actual = (
        history.assign(month=history.month.dt.strftime("%Y-%m-%d"))
        .set_index(["customer_id", "month"])
        .deposit_balance.sort_index()
    )
    assert actual.tolist() == expected.tolist()
    assert str(history.month.dtype).startswith("datetime64")
    assert history.has_loan.dtype == bool
    assert len(repository.periods()) == 24
    assert len(repository.managers()) == 20


def test_filters_and_parameterization(repository, dataset):
    expected = dataset[1]["customers"]
    subset = repository.customers(Filters(rm_id="SYN-RM001"))
    assert (
        subset.customer_id.tolist()
        == expected[expected.rm_id == "SYN-RM001"].customer_id.tolist()
    )
    assert len(repository.snapshot("2025-12-01", Filters(rm_id="SYN-RM001"))) == len(
        subset
    )
    assert repository.customers(Filters(industry="' OR 1=1 --")).empty
    assert repository.history(customer_id="' OR 1=1 --").empty
    region = expected.region.iloc[0]
    assert len(repository.customers(Filters(region=region))) == int(
        (expected.region == region).sum()
    )


def test_missing_unknown_and_dates(repository, tmp_path):
    with (
        pytest.raises(FileNotFoundError, match="banking-data generate"),
        analytics_connection(tmp_path),
    ):
        pass
    with pytest.raises(LookupError, match="Unknown customer"):
        repository.profile("unknown")
    with pytest.raises(ValueError, match="first-of-month"):
        repository.snapshot("2025-12-02")
    with pytest.raises(ValueError, match="No data"):
        repository.snapshot("2026-01-01")
    with pytest.raises(ValueError, match="Start month"):
        repository.history(start="2025-12-01", end="2024-01-01")


def test_default_path_independent_of_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert Settings().data_dir == PROJECT_ROOT / "data" / "synthetic"


@pytest.mark.parametrize("defect", ["duplicate", "unknown", "missing_period"])
def test_reject_bad_join_inputs(dataset, tmp_path, defect):
    tables = {name: frame.copy() for name, frame in dataset[1].items()}
    if defect == "duplicate":
        tables["loans"] = pd.concat([tables["loans"], tables["loans"].iloc[:1]])
    elif defect == "unknown":
        tables["loans"].loc[0, "customer_id"] = "UNKNOWN"
    else:
        tables["loans"] = tables["loans"].iloc[1:]
    for name, frame in tables.items():
        frame.to_csv(tmp_path / f"{name}.csv", index=False)
    with pytest.raises(DataValidationError), analytics_connection(tmp_path):
        pass
