import duckdb
import streamlit as st

from rm_hub.data.connection import DataValidationError
from streamlit_app.components import (
    concentration_chart,
    financial_metrics,
    line_chart,
    product_chart,
)
from streamlit_app.data import data_directory, fingerprint, load_options, load_portfolio


def data_error(message):
    st.error(message)
    st.caption(
        "Generate or validate the synthetic CSVs from the project root, then refresh this page."
    )
    st.code(
        "python -m uv run banking-data generate\npython -m uv run banking-data validate",
        language="powershell",
    )


def render():
    st.title("Portfolio Overview")
    st.caption(
        "Understand relationship balances, bank profitability, and product adoption."
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
            "The synthetic dataset could not be read. Check file schemas and data integrity."
        )
        return

    managers = options["managers"].set_index("rm_id").rm_name.to_dict()
    customers = options["customers"]
    with st.sidebar:
        st.subheader("Portfolio filters")
        month = st.selectbox(
            "Reporting month",
            options["periods"],
            index=len(options["periods"]) - 1,
            format_func=lambda value: value.strftime("%B %Y"),
            key="reporting_month",
        )
        rm_id = st.selectbox(
            "Relationship manager",
            [None, *managers],
            format_func=lambda value: (
                "All relationship managers" if value is None else managers[value]
            ),
            key="rm_filter",
        )
        industry = st.selectbox(
            "Industry",
            [None, *sorted(customers.industry.unique())],
            format_func=lambda value: "All industries" if value is None else value,
            key="industry_filter",
        )
        region = st.selectbox(
            "Region",
            [None, *sorted(customers.region.unique())],
            format_func=lambda value: "All regions" if value is None else value,
            key="region_filter",
        )
        st.caption("Filters combine across all metrics, charts, and tables.")

    try:
        with st.spinner("Preparing portfolio insights…"):
            bundle = load_portfolio(
                str(directory), signature, month, rm_id, industry, region
            )
    except (DataValidationError, duckdb.Error, ValueError, OSError):
        data_error(
            "Portfolio calculations could not be completed. Validate the synthetic data and retry."
        )
        return

    st.markdown(f"**{month:%B %Y}** · USD · Trends through the selected month")
    if bundle["summary"]["customer_count"] == 0:
        st.info(
            "No customers match these filters. Broaden the RM, industry, or region selection."
        )
        return

    financial_metrics(bundle["summary"])
    st.caption(
        "Balances are month-end snapshots. Revenue, expenses, and profitability are monthly bank relationship flows."
    )
    st.divider()

    left, right = st.columns(2)
    with left:
        st.subheader("Relationship balances")
        st.plotly_chart(
            line_chart(
                bundle["trends"], ["deposit_balance", "loan_balance", "card_balance"]
            ),
            width="stretch",
            key="balance_trends",
        )
    with right:
        st.subheader("Bank relationship economics")
        st.plotly_chart(
            line_chart(
                bundle["trends"],
                ["total_revenue", "allocated_expenses", "profitability"],
            ),
            width="stretch",
            key="economics_trends",
        )

    left, right = st.columns(2)
    with left:
        st.subheader("Deposit concentration")
        industry_tab, rm_tab = st.tabs(["By industry", "By relationship manager"])
        with industry_tab:
            st.plotly_chart(
                concentration_chart(bundle["industry"], "industry"),
                width="stretch",
                key="industry_concentration",
            )
        with rm_tab:
            rm_frame = bundle["rm"].assign(
                rm_name=lambda frame: frame.rm_id.map(managers)
            )
            st.plotly_chart(
                concentration_chart(rm_frame, "rm_name"),
                width="stretch",
                key="rm_concentration",
            )
    with right:
        st.subheader("Product penetration")
        st.plotly_chart(
            product_chart(bundle["summary"]["product_penetration_percent"]),
            width="stretch",
            key="product_penetration",
        )
        st.caption("Share of selected customers holding each product.")

    with st.expander("Portfolio concentration details"):
        st.dataframe(
            bundle["industry"]
            .rename(
                columns={
                    "industry": "Industry",
                    "customer_count": "Customers",
                    "deposit_balance": "Deposits (USD)",
                    "loan_balance": "Loans (USD)",
                    "card_balance": "Credit cards (USD)",
                    "total_revenue": "Bank revenue (USD)",
                    "allocated_expenses": "Allocated expenses (USD)",
                    "profitability": "Bank profitability (USD)",
                    "deposit_share_percent": "Deposit share (%)",
                }
            )
            .round(2),
            hide_index=True,
            width="stretch",
        )

    with st.expander("Customer portfolio"):
        columns = [
            "customer_id",
            "business_name",
            "rm_name",
            "industry",
            "deposit_balance",
            "loan_balance",
            "card_balance",
            "profitability",
            "attrition_indicator",
        ]
        st.dataframe(
            bundle["snapshot"][columns].rename(
                columns={
                    "customer_id": "Customer ID",
                    "business_name": "Fictional business",
                    "rm_name": "Relationship manager",
                    "industry": "Industry",
                    "deposit_balance": "Deposits (USD)",
                    "loan_balance": "Loans (USD)",
                    "card_balance": "Credit cards (USD)",
                    "profitability": "Bank profitability (USD)",
                    "attrition_indicator": "Deposit decline flag",
                }
            ),
            hide_index=True,
            width="stretch",
        )
