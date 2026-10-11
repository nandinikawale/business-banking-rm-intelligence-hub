import pandas as pd

from .portfolio import HOLDINGS


def customer_360(repository, customer_id, month=None):
    profile = repository.profile(customer_id)
    selected = repository.resolve_month(month)
    history = repository.history(customer_id=customer_id, end=selected)
    current = history[history.month == pd.Timestamp(selected)]
    if current.empty:
        raise LookupError(f"No history for {customer_id} in {selected}")
    changes = []
    for index in range(1, len(history)):
        old, new = history.iloc[index - 1], history.iloc[index]
        for product in HOLDINGS:
            if bool(old[product]) != bool(new[product]):
                changes.append(
                    {
                        "month": new.month,
                        "product": product,
                        "change": "Added" if new[product] else "Removed",
                    }
                )
    return {
        "profile": profile,
        "month": selected,
        "snapshot": current.iloc[0].to_dict(),
        "history": history.reset_index(drop=True),
        "product_changes": pd.DataFrame(
            changes, columns=["month", "product", "change"]
        ),
    }
