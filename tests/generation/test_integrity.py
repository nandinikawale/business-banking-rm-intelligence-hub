import pytest

from banking_data.cli import generate
from banking_data.config import Config
from banking_data.export import write_outputs
from banking_data.indicators import sustained_decline
from banking_data.validation import validate


@pytest.fixture(scope="module")
def sample():
    config = Config(customers=30)
    tables, scenarios = generate(config)
    return config, tables, scenarios


def test_financial_and_relationship_integrity(sample):
    config, tables, _ = sample
    assert validate(tables, config)["passed"]


def test_reject_profit_mismatch(sample):
    config, tables, _ = sample
    changed = {name: frame.copy() for name, frame in tables.items()}
    changed["profitability"].loc[0, "profitability"] += 0.01
    with pytest.raises(ValueError, match="Bank profitability"):
        validate(changed, config)


def test_reject_unknown_customer(sample):
    config, tables, _ = sample
    changed = {name: frame.copy() for name, frame in tables.items()}
    changed["loans"].loc[0, "customer_id"] = "UNKNOWN"
    with pytest.raises(ValueError, match="keys"):
        validate(changed, config)


def test_attrition_boundaries():
    assert sustained_decline([10000, 9000, 8500, 8000])
    assert not sustained_decline([10000, 9000, 9200, 7000])
    assert not sustained_decline([10000, 9500, 9000])
    assert not sustained_decline([9000, 8000, 7000, 6000])
    assert not sustained_decline([10000, 9800, 9700, 9600])


def test_csv_reproducibility(sample, tmp_path):
    config, tables, scenarios = sample
    report = validate(tables, config)
    again, labels = generate(config)
    for directory, frames, simulation in [
        ("a", tables, scenarios),
        ("b", again, labels),
    ]:
        write_outputs(
            frames,
            config,
            report,
            simulation,
            tmp_path / directory,
            tmp_path / (directory + "_reports"),
        )
    for first in (tmp_path / "a").glob("*.csv"):
        assert first.read_bytes() == (tmp_path / "b" / first.name).read_bytes()


def test_attrition_scenarios_have_sustained_outflows(sample):
    _, tables, scenarios = sample
    ids = [key for key, value in scenarios.items() if value == "attrition"]
    assert ids
    deposits = tables["deposits"]
    for customer in ids:
        history = deposits[deposits.customer_id == customer].sort_values("month")
        assert history.iloc[-1].closing_balance < history.iloc[14].closing_balance * 0.5
        assert history.iloc[18:].attrition_indicator.all()
