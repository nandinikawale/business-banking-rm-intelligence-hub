import duckdb
import streamlit as st

from rm_hub.data.connection import DataValidationError
from rm_hub.services.opportunities import (
    filter_opportunities,
    opportunity_breakdown,
    opportunity_summary,
)
from streamlit_app.components import (
    OPPORTUNITY_PRODUCTS,
    metric_card,
    signal_distribution_chart,
)
from streamlit_app.data import (
    data_directory,
    fingerprint,
    load_opportunities,
    load_options,
)
from streamlit_app.views.portfolio_overview import data_error


def render():
    st.title("RM Opportunities")
    st.caption(
        "An explainable review list for fictional retention and product opportunities."
    )
    directory = data_directory()
    try:
        signature = fingerprint(directory)
        with st.spinner("Reading the synthetic portfolio…"):
            options = load_options(str(directory), signature)
    except FileNotFoundError as error:
        data_error(str(error))
        return
    except (DataValidationError, duckdb.Error, ValueError, OSError):
        data_error(
            "The synthetic dataset could not be read. Validate the CSVs and retry."
        )
        return
    managers = options["managers"].set_index("rm_id").rm_name.to_dict()
    customers = options["customers"]
    with st.sidebar:
        st.subheader("Opportunity filters")
        month = st.selectbox(
            "Reporting month",
            options["periods"],
            index=len(options["periods"]) - 1,
            format_func=lambda value: value.strftime("%B %Y"),
            key="opp_month",
        )
        rm_id = st.selectbox(
            "Relationship manager",
            [None, *managers],
            format_func=lambda value: (
                "All relationship managers" if value is None else managers[value]
            ),
            key="opp_rm",
        )
        industry = st.selectbox(
            "Industry",
            [None, *sorted(customers.industry.unique())],
            format_func=lambda value: "All industries" if value is None else value,
            key="opp_industry",
        )
        region = st.selectbox(
            "Region",
            [None, *sorted(customers.region.unique())],
            format_func=lambda value: "All regions" if value is None else value,
            key="opp_region",
        )
        signal_type = st.selectbox(
            "Signal type",
            [None, "Retention", "Cross-sell"],
            format_func=lambda value: "All signals" if value is None else value,
            key="opp_type",
        )
        product = st.selectbox(
            "Product",
            [None, *OPPORTUNITY_PRODUCTS],
            format_func=lambda value: (
                "All products" if value is None else OPPORTUNITY_PRODUCTS[value]
            ),
            key="opp_product",
        )
        st.caption("All counts, charts, and rows reflect the same filters.")

    try:
        with st.spinner("Preparing the review list…"):
            signals = load_opportunities(
                str(directory), signature, month, rm_id, industry, region
            )
            selected = filter_opportunities(signals, signal_type, product)
    except (DataValidationError, duckdb.Error, ValueError, OSError):
        data_error(
            "Opportunity calculations could not be completed. Validate the data and retry."
        )
        return
    summary = opportunity_summary(selected)
    st.markdown(f"**{month:%B %Y}** · Observations through the selected month")
    columns = st.columns(4)
    for column, key, label, help_text in [
        (
            columns[0],
            "signal_count",
            "Total signals",
            "One row per customer and signal. A customer can have multiple signals.",
        ),
        (
            columns[1],
            "customer_count",
            "Customers with signals",
            "Distinct fictional customers represented in the filtered review list.",
        ),
        (
            columns[2],
            "retention_signal_count",
            "Retention reviews",
            "Sustained deposit-decline signals in the selected month.",
        ),
        (
            columns[3],
            "cross_sell_signal_count",
            "Cross-sell signals",
            "Missing products that meet the documented fictional activity thresholds.",
        ),
    ]:
        metric_card(column, label, f"{summary[key]:,}", help_text)
    st.caption(
        "Signal counts are not customer counts. Multiple product signals can belong to the same customer."
    )
    if selected.empty:
        st.info(
            "No signals match these filters. Broaden the selection or choose another reporting month."
        )
        return

    left, right = st.columns(2)
    with left:
        st.subheader("Signals by relationship manager")
        st.plotly_chart(
            signal_distribution_chart(opportunity_breakdown(selected, "rm"), "rm"),
            width="stretch",
            key="opportunities_by_rm",
        )
    with right:
        st.subheader("Signals by product")
        st.plotly_chart(
            signal_distribution_chart(
                opportunity_breakdown(selected, "product"), "product"
            ),
            width="stretch",
            key="opportunities_by_product",
        )

    st.subheader("Prioritized review list")
    st.caption(
        "Default review order: retention first, then cross-sell. This is a display convention, not a risk score."
    )
    display = selected.copy()
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
    display = display[
        [
            "review_order",
            "customer_id",
            "business_name",
            "rm_name",
            "signal_type",
            "product",
            "activity_value",
            "rule_threshold",
            "deposit_change_percent",
            "reason",
            "month",
        ]
    ].rename(
        columns={
            "review_order": "Review order",
            "customer_id": "Customer ID",
            "business_name": "Fictional business",
            "rm_name": "Relationship manager",
            "signal_type": "Signal type",
            "product": "Potential product",
            "activity_value": "Activity (USD)",
            "rule_threshold": "Rule threshold",
            "deposit_change_percent": "Deposit change (%)",
            "reason": "Supporting observation",
            "month": "Reporting month",
        }
    )
    st.dataframe(
        display,
        hide_index=True,
        width="stretch",
        height=425,
        column_order=[
            "Review order",
            "Customer ID",
            "Potential product",
            "Supporting observation",
            "Relationship manager",
            "Fictional business",
            "Signal type",
            "Rule threshold",
            "Activity (USD)",
            "Deposit change (%)",
            "Reporting month",
        ],
        column_config={
            "Activity (USD)": st.column_config.NumberColumn(format="dollar"),
            "Deposit change (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Supporting observation": st.column_config.TextColumn(width=400),
            "Review order": st.column_config.TextColumn(width=100),
            "Customer ID": st.column_config.TextColumn(width=130),
            "Potential product": st.column_config.TextColumn(width=170),
            "Relationship manager": st.column_config.TextColumn(width=180),
        },
    )
    st.caption(
        "Scroll right for business details and numeric evidence. Activity is closing deposits for retention/treasury signals and monthly business sales for other product signals. Percentages and USD thresholds use separate units."
    )

    with st.expander("How these demonstration rules work"):
        st.markdown("""
        - **Retention:** three consecutive declines totaling at least 20%, starting from deposits of at least USD 10,000. Four consecutive monthly observations are required.
        - **Merchant services:** product absent and monthly business sales at least USD 50,000.
        - **Payroll services:** product absent and monthly business sales at least USD 80,000.
        - **Treasury services:** product absent and closing deposits at least USD 200,000.
        - **Credit card:** product absent and monthly business sales at least USD 25,000.
        """)
        st.caption(
            "Signals use observed synthetic measures, not hidden scenario labels or future data. They are review prompts, not predictions, suitability assessments, or credit decisions."
        )


if __name__ == "__main__":
    render()
