"""Read-only analytics demonstration; run from the project root."""

import json

from rm_hub.data.connection import analytics_connection
from rm_hub.data.repository import Repository
from rm_hub.services.customer import customer_360
from rm_hub.services.opportunities import opportunities
from rm_hub.services.portfolio import portfolio_summary


def main():
    with analytics_connection() as connection:
        repository = Repository(connection)
        print(json.dumps(portfolio_summary(repository), indent=2, default=str))
        customer_id = repository.customers().iloc[0].customer_id
        customer = customer_360(repository, customer_id)
        print(
            f"Customer {customer_id}: {len(customer['history'])} monthly observations"
        )
        signals = opportunities(repository)
        print("Opportunity counts:")
        print(signals.groupby("signal_type").size().to_string())
        print("First five signals:")
        print(
            signals[["customer_id", "signal_type", "product", "reason"]]
            .head()
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()
