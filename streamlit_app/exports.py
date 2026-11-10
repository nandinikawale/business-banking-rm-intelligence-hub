"""Presentation formatting and CSV serialization for the opportunity worklist."""

from streamlit_app.components import OPPORTUNITY_PRODUCTS

WORKLIST_LABELS = {
    "review_order": "Review order",
    "customer_id": "Customer ID",
    "business_name": "Fictional business",
    "rm_name": "Relationship manager",
    "industry": "Industry",
    "region": "Region",
    "signal_type": "Signal type",
    "product": "Potential product",
    "activity_value": "Activity (USD)",
    "rule_threshold": "Rule threshold",
    "deposit_change_percent": "Deposit change (%)",
    "reason": "Supporting observation",
    "month": "Reporting month",
}


def opportunity_worklist(signals):
    """Use one formatted worklist for the table and the dedicated CSV download."""
    display = signals.copy()
    display["review_order"] = display.priority.map(
        {1: "1 · Retention", 2: "2 · Cross-sell"}
    )
    display["product"] = display["product"].map(OPPORTUNITY_PRODUCTS)
    display["rule_threshold"] = [
        f"At least {threshold:.0f}% decline"
        if kind == "Retention"
        else f"At least USD {threshold:,.0f}"
        for kind, threshold in zip(display.signal_type, display.threshold)
    ]
    display["month"] = display.month.dt.strftime("%B %Y")
    return display[list(WORKLIST_LABELS)].rename(columns=WORKLIST_LABELS)


def worklist_csv(display):
    """UTF-8 BOM supports Excel; quote CSV normally and neutralize text formulas."""
    safe = display.copy()
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(
            lambda value: (
                "'" + value
                if isinstance(value, str)
                and value.lstrip().startswith(("=", "+", "-", "@"))
                else value
            )
        )
    return safe.to_csv(index=False, float_format="%.2f").encode("utf-8-sig")
