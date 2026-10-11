import duckdb
import pandas as pd
import streamlit as st

from rm_hub.data.connection import DataValidationError
from rm_hub.services.portfolio import HOLDINGS
from streamlit_app.components import LABELS, currency, line_chart, metric_card
from streamlit_app.data import data_directory, fingerprint, load_customer, load_options
from streamlit_app.views.portfolio_overview import data_error


def render():
    st.title("Customer 360")
    st.caption(
        "Explore one fictional business relationship, its finances, and product history."
    )
    directory = data_directory()
    try:
        signature = fingerprint(directory)
        with st.spinner("Reading customer profiles…"):
            options = load_options(str(directory), signature)
    except FileNotFoundError as error:
        data_error(str(error))
        return
    except (DataValidationError, duckdb.Error, ValueError, OSError):
        data_error(
            "The synthetic dataset could not be read. Validate the CSVs and retry."
        )
        return

    customers = options["customers"]
    if customers.empty:
        st.info("No fictional customer profiles are available.")
        return
    names = customers.set_index("customer_id").business_name.to_dict()
    with st.sidebar:
        st.subheader("Customer selection")
        customer_id = st.selectbox(
            "Fictional business",
            list(names),
            format_func=lambda value: f"{names[value]} · {value}",
            key="customer_id",
        )
        month = st.selectbox(
            "Reporting month",
            options["periods"],
            index=len(options["periods"]) - 1,
            format_func=lambda value: value.strftime("%B %Y"),
            key="customer_month",
        )
        st.caption("Type a business name or customer ID in the selector to search.")

    try:
        with st.spinner("Preparing customer insights…"):
            bundle = load_customer(str(directory), signature, customer_id, month)
    except (LookupError, DataValidationError, duckdb.Error, ValueError, OSError):
        data_error(
            "This customer's history could not be read. Validate the data and refresh."
        )
        return

    profile, snapshot, history = (
        bundle["profile"],
        bundle["snapshot"],
        bundle["history"],
    )
    st.subheader(profile["business_name"])
    st.caption(
        f"{customer_id} · {month:%B %Y} · USD · History through the selected month"
    )

    with st.container(border=True):
        first = st.columns(3)
        for column, label, value in [
            (first[0], "Industry", profile["industry"]),
            (first[1], "Business size", profile["business_size"]),
            (first[2], "Region", profile["region"]),
        ]:
            column.markdown(f"**{label}**")
            column.write(value)
        second = st.columns(3)
        for column, label, value in [
            (second[0], "Relationship manager", profile["rm_name"]),
            (
                second[1],
                "Relationship since",
                pd.Timestamp(profile["relationship_start_month"]).strftime("%B %Y"),
            ),
            (
                second[2],
                "Business age at January 2024",
                f"{profile['business_age_years']} years",
            ),
        ]:
            column.markdown(f"**{label}**")
            column.write(value)

    first = st.columns(4)
    for column, key in zip(
        first[:3], ["deposit_balance", "loan_balance", "card_balance"]
    ):
        metric_card(
            column,
            LABELS[key],
            currency(snapshot[key]),
            f"Closing balance: USD {snapshot[key]:,.2f}.",
        )
    metric_card(
        first[3],
        "Products held",
        f"{snapshot['product_count']} / {len(HOLDINGS)}",
        "Products held in the selected reporting month.",
    )
    second = st.columns(4)
    for column, key in zip(
        second[:3], ["total_revenue", "allocated_expenses", "profitability"]
    ):
        metric_card(
            column,
            LABELS[key],
            currency(snapshot[key]),
            f"Monthly bank relationship amount: USD {snapshot[key]:,.2f}.",
        )
    metric_card(
        second[3],
        "Deposit decline flag",
        "Review" if snapshot["attrition_indicator"] else "Not triggered",
        "A rule-based review indicator from sustained deposit declines, not a probability or prediction.",
    )
    if not snapshot["has_loan"]:
        st.caption("This customer has no loan holding in the selected month.")
    if not snapshot["has_credit_card"]:
        st.caption("This customer has no credit card holding in the selected month.")

    left, right = st.columns(2)
    with left:
        st.subheader("Relationship balances")
        st.plotly_chart(
            line_chart(history, ["deposit_balance", "loan_balance", "card_balance"]),
            width="stretch",
            key="customer_balance_chart",
        )
    with right:
        st.subheader("Bank relationship economics")
        st.plotly_chart(
            line_chart(
                history, ["total_revenue", "allocated_expenses", "profitability"]
            ),
            width="stretch",
            key="customer_bank_chart",
        )
    st.caption(
        "Bank profitability is bank revenue minus allocated expenses. It is separate from the business's operating profit."
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Product holdings")
        holdings = pd.DataFrame(
            [
                {
                    "Product": LABELS[key],
                    "Status": "Held" if snapshot[key] else "Not held",
                }
                for key in HOLDINGS
            ]
        )
        st.dataframe(holdings, hide_index=True, width="stretch")
    with right:
        st.subheader("Product changes")
        changes = bundle["product_changes"]
        if changes.empty:
            st.caption("No product changes recorded through this month.")
        else:
            display = changes.assign(
                month=changes.month.dt.strftime("%B %Y"),
                product=changes["product"].map(LABELS),
            ).rename(
                columns={"month": "Month", "product": "Product", "change": "Change"}
            )
            st.dataframe(display, hide_index=True, width="stretch")

    st.subheader("Relationship review")
    signals = bundle["signals"]
    retention = signals[signals.signal_type == "Retention"]
    if len(history) < 4:
        st.info(
            "At least four monthly observations are required for the deposit-decline rule."
        )
    elif retention.empty:
        st.info("The sustained deposit-decline rule was not triggered for this month.")
    else:
        for reason in retention.reason:
            st.warning(reason)
    cross_sell = signals[signals.signal_type == "Cross-sell"]
    if cross_sell.empty:
        st.caption(
            "No product cross-sell signals meet the demonstration rules in this month."
        )
    else:
        st.dataframe(
            cross_sell[["product", "reason"]]
            .assign(
                product=lambda frame: frame["product"].str.replace("_", " ").str.title()
            )
            .rename(
                columns={
                    "product": "Potential product",
                    "reason": "Supporting observation",
                }
            ),
            hide_index=True,
            width="stretch",
        )
    st.caption(
        "These indicators use documented fictional thresholds. They are review prompts, not credit decisions or predictions."
    )

    with st.expander("Business operating performance"):
        st.caption(
            "Fictional customer operating results, before financing charges; these are not bank revenues."
        )
        columns = st.columns(3)
        for column, key in zip(
            columns, ["business_revenue", "business_expenses", "business_profit"]
        ):
            metric_card(
                column,
                LABELS[key],
                currency(snapshot[key]),
                f"Monthly business amount: USD {snapshot[key]:,.2f}.",
            )
        st.plotly_chart(
            line_chart(
                history, ["business_revenue", "business_expenses", "business_profit"]
            ),
            width="stretch",
            key="customer_business_chart",
        )

    with st.expander("Monthly financial history"):
        columns = [
            "month",
            "deposit_balance",
            "loan_balance",
            "card_balance",
            "total_revenue",
            "allocated_expenses",
            "profitability",
            "business_revenue",
            "business_expenses",
            "business_profit",
        ]
        display = history[columns].assign(month=history.month.dt.strftime("%Y-%m"))
        display = display.rename(
            columns={
                "month": "Month",
                **{key: f"{LABELS[key]} (USD)" for key in columns[1:]},
            }
        )
        st.dataframe(display, hide_index=True, width="stretch")


if __name__ == "__main__":
    render()
