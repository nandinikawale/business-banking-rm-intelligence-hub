"""Reusable presentation for deposit movement and bank profitability insights."""

import plotly.graph_objects as go
import streamlit as st

from rm_hub.services.relationship_insights import deposit_contributors
from streamlit_app.components import COLORS, currency, metric_card

DECREASE = "#b54750"


def signed_currency(value):
    return ("-" if value < 0 else "") + currency(abs(value))


def deposit_movement_chart(contributors):
    return go.Figure(
        go.Bar(
            x=contributors.deposit_change.tolist(),
            y=contributors.label.tolist(),
            orientation="h",
            marker_color=[
                DECREASE if value < 0 else COLORS[0]
                for value in contributors.deposit_change
            ],
            customdata=contributors[
                ["business_name", "customer_count"]
            ].values.tolist(),
            hovertemplate=(
                "%{y}<br>%{customdata[0]}<br>Change: USD %{x:,.2f}"
                "<br>Customers represented: %{customdata[1]}<extra></extra>"
            ),
        )
    ).update_layout(
        template="plotly_white",
        height=max(310, 100 + 29 * len(contributors)),
        margin={"l": 12, "r": 12, "t": 10, "b": 10},
        xaxis={"title": "Deposit change (USD)", "tickprefix": "$", "zeroline": True},
        yaxis={"title": None, "autorange": "reversed", "automargin": True},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )


def render_deposit_movement(bundle):
    st.subheader("What drove the deposit change?")
    if not bundle["available"]:
        st.info("No previous-month data is available for this comparison.")
        return
    st.caption(
        f"{bundle['month']:%B %Y} vs {bundle['previous_month']:%B %Y} · "
        "Same filtered customers · Closing deposit balances"
    )
    columns = st.columns(3)
    for column, key, label in zip(
        columns,
        ["increases", "decreases", "net_change"],
        ["Deposit increases", "Deposit decreases", "Net deposit change"],
    ):
        metric_card(
            column,
            label,
            signed_currency(bundle[key]),
            "Sum of customer-level closing balance changes within the selected filters.",
        )
    contributors = deposit_contributors(bundle["details"])
    if bundle["details"].deposit_change.ne(0).any():
        st.plotly_chart(
            deposit_movement_chart(contributors),
            width="stretch",
            key="deposit_movement_chart",
        )
    else:
        st.info("Deposit balances are unchanged from the previous month.")
    st.caption(
        "The chart shows up to five increases and five decreases. Other customers "
        "(net) includes every remaining customer, including offsetting changes. "
        "All contributions reconcile to the net deposit change. Red bars are decreases; teal bars are increases."
    )
    with st.expander("Customer deposit movement details"):
        st.dataframe(
            bundle["details"].rename(
                columns={
                    "customer_id": "Customer ID",
                    "business_name": "Fictional business",
                    "rm_name": "Relationship manager",
                    "industry": "Industry",
                    "region": "Region",
                    "previous_balance": "Previous deposits (USD)",
                    "current_balance": "Selected-month deposits (USD)",
                    "deposit_change": "Deposit change (USD)",
                    "deposit_change_percent": "Deposit change (%)",
                }
            ),
            hide_index=True,
            width="stretch",
            column_config={
                **{
                    key: st.column_config.NumberColumn(format="dollar")
                    for key in [
                        "Previous deposits (USD)",
                        "Selected-month deposits (USD)",
                        "Deposit change (USD)",
                    ]
                },
                "Deposit change (%)": st.column_config.NumberColumn(format="%.2f%%"),
            },
        )
        st.caption("Percentage change is unavailable when previous deposits are zero.")


def profitability_waterfall(components):
    indexed = components.set_index("key")
    keys = [
        "deposit_revenue",
        "lending_revenue",
        "card_revenue",
        "service_fee_revenue",
        "allocated_expenses",
        "profitability",
    ]
    amounts = indexed.loc[keys, "current"].tolist()
    amounts[-2] *= -1
    return go.Figure(
        go.Waterfall(
            x=[
                "Deposit",
                "Lending",
                "Card",
                "Services",
                "Allocated<br>costs",
                "Bank<br>profitability",
            ],
            y=[*amounts[:-1], 0],
            measure=["relative"] * 5 + ["total"],
            customdata=amounts,
            increasing={"marker": {"color": COLORS[0]}},
            decreasing={"marker": {"color": DECREASE}},
            totals={"marker": {"color": COLORS[1]}},
            connector={"line": {"color": "#aebbc9"}},
            hovertemplate="%{x}<br>USD %{customdata:,.2f}<extra></extra>",
        )
    ).update_layout(
        template="plotly_white",
        height=370,
        showlegend=False,
        margin={"l": 12, "r": 12, "t": 15, "b": 15},
        yaxis={"title": "Monthly bank relationship amount (USD)", "tickprefix": "$"},
        xaxis={"type": "category"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )


def render_profitability_breakdown(bundle):
    st.subheader("What makes up bank profitability?")
    st.caption(
        "Monthly bank revenue components minus allocated costs; "
        "separate from the customer's operating profit."
    )
    components = bundle["components"]
    left, right = st.columns([1.3, 1])
    with left:
        st.plotly_chart(
            profitability_waterfall(components),
            width="stretch",
            key="profitability_waterfall",
        )
    with right:
        st.markdown("**Why did profitability change?**")
        totals = components[components.kind.eq("Total")].copy()
        if bundle["has_previous"]:
            st.caption(f"{bundle['previous_month']:%B %Y} → {bundle['month']:%B %Y}")
            comparison = totals[["component", "previous", "current", "change"]]
        else:
            st.info("No previous-month data is available for this comparison.")
            comparison = totals[["component", "current"]]
        st.dataframe(
            comparison.rename(
                columns={
                    "component": "Measure",
                    "previous": "Prior (USD)",
                    "current": "Current (USD)",
                    "change": "Change (USD)",
                }
            ),
            hide_index=True,
            width="stretch",
            column_config={
                "Measure": st.column_config.TextColumn(width="medium"),
                **{
                    name: st.column_config.NumberColumn(format="$%.2f", width="small")
                    for name in ["Prior (USD)", "Current (USD)", "Change (USD)"]
                },
            },
        )
        indexed = totals.set_index("key")
        equation = (
            f"**{currency(indexed.loc['total_revenue', 'current'])} revenue − "
            f"{currency(indexed.loc['allocated_expenses', 'current'])} allocated costs = "
            f"{signed_currency(indexed.loc['profitability', 'current'])} bank profitability**"
        )
        st.markdown(equation.replace("$", r"\$"))
    with st.expander("Revenue and allocated cost details"):
        details = components[~components.kind.eq("Total")][
            ["component", "kind", "previous", "current", "change", "profit_impact"]
        ]
        st.dataframe(
            details.rename(
                columns={
                    "component": "Component",
                    "kind": "Type",
                    "previous": "Prior (USD)",
                    "current": "Current (USD)",
                    "change": "Amount change (USD)",
                    "profit_impact": "Impact on profit (USD)",
                }
            ),
            hide_index=True,
            width="stretch",
            height=355,
            column_config={
                name: st.column_config.NumberColumn(format="$%.2f")
                for name in [
                    "Prior (USD)",
                    "Current (USD)",
                    "Amount change (USD)",
                    "Impact on profit (USD)",
                ]
            },
        )
        st.caption(
            "Amounts are positive for revenue and cost components. An increase in cost "
            "reduces profit, so its profit impact has the opposite sign. Deposit revenue "
            "already includes deposit interest expense; that expense is not deducted again."
        )
