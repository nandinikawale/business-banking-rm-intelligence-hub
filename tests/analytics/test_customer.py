import itertools

import pytest

from rm_hub.services.customer import customer_360


def test_customer_profile_history_and_no_future_data(repository, dataset):
    customer_id = dataset[1]["customers"].customer_id.iloc[0]
    result = customer_360(repository, customer_id, "2024-06-01")
    assert result["profile"]["customer_id"] == customer_id
    assert len(result["history"]) == 6
    assert result["history"].month.is_monotonic_increasing
    assert result["snapshot"]["month"].strftime("%Y-%m-%d") == "2024-06-01"
    assert "business_profit" in result["snapshot"]
    assert "profitability" in result["snapshot"]
    assert result["history"].customer_id.nunique() == 1
    assert result["product_changes"].empty


def test_product_adoptions_match_history(repository, dataset):
    products = dataset[1]["products"]
    expected = []
    for customer_id, frame in products.groupby("customer_id"):
        flags = frame.has_payroll_services.tolist()
        if any(a != b for a, b in itertools.pairwise(flags)):
            expected.append(customer_id)
    assert expected
    result = customer_360(repository, expected[0])
    assert "has_payroll_services" in result["product_changes"]["product"].tolist()
    assert result["product_changes"].iloc[0].month.strftime("%Y-%m-%d") == "2025-01-01"


def test_unknown_customer(repository):
    with pytest.raises(LookupError):
        customer_360(repository, "UNKNOWN")
