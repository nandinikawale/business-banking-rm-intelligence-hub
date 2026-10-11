import plotly.graph_objects as go
import streamlit as st

COLORS = ["#087f8c", "#3757a8", "#c08b33"]
LABELS = {
    "business_revenue": "Business sales",
    "business_expenses": "Operating expenses",
    "business_profit": "Operating profit",
    "deposit_balance": "Deposits",
    "loan_balance": "Loans",
    "card_balance": "Credit cards",
    "total_revenue": "Bank revenue",
    "allocated_expenses": "Allocated expenses",
    "profitability": "Bank profitability",
    "has_deposit_account": "Deposits",
    "has_loan": "Loans",
    "has_credit_card": "Credit cards",
    "has_merchant_services": "Merchant services",
    "has_payroll_services": "Payroll services",
    "has_treasury_services": "Treasury services",
}


def currency(value):
    if abs(value) >= 1000000:
        return f"${value / 1000000:,.2f}M"
    if abs(value) >= 1000:
        return f"${value / 1000:,.1f}K"
    return f"${value:,.2f}"


def apply_style():
    st.markdown(
        """
        <style>
        .block-container {padding-top: 4.5rem; padding-bottom: 3rem; max-width: 1500px;}
        h1 {letter-spacing: -0.035em;}
        [data-testid="stMetric"] {min-height: 92px;}
        [data-testid="stMetricValue"] {font-size: 1.8rem; font-weight: 650;}
        [data-testid="stMetricLabel"] {color: #52647a;}
        [data-testid="stSidebar"] {border-right: 1px solid #e5eaf1;}
        </style>
    """,
        unsafe_allow_html=True,
    )


def metric_card(column, label, value, help_text, delta=None, inverse=False):
    with column.container(border=True):
        st.metric(
            label,
            value,
            delta=delta,
            delta_color="inverse" if inverse else "normal",
            help=help_text,
        )


def financial_metrics(summary):
    first = st.columns(4)
    metric_card(
        first[0],
        "Customers",
        f"{summary['customer_count']:,}",
        "Fictional businesses matching all selected filters.",
    )
    for column, key in zip(
        first[1:], ["deposit_balance", "loan_balance", "card_balance"]
    ):
        change = summary["month_over_month"][key]["percent"]
        delta = None if change is None else f"{change:+.2f}% vs prior month"
        metric_card(
            column,
            LABELS[key],
            currency(summary[key]),
            f"Selected-month closing balance: USD {summary[key]:,.2f}.",
            delta,
        )
    second = st.columns(4)
    for column, key in zip(
        second[:3], ["total_revenue", "allocated_expenses", "profitability"]
    ):
        change = summary["month_over_month"][key]["percent"]
        delta = None if change is None else f"{change:+.2f}% vs prior month"
        metric_card(
            column,
            LABELS[key],
            currency(summary[key]),
            f"Selected-month bank relationship measure: USD {summary[key]:,.2f}.",
            delta,
            inverse=key == "allocated_expenses",
        )
    metric_card(
        second[3],
        "Deposit decline flags",
        f"{summary['attrition_customer_count']:,}",
        "Three consecutive deposit declines of at least 20% combined, with a starting balance of USD 10,000 or more. A review indicator, not a prediction.",
    )


def line_chart(frame, metrics):
    figure = go.Figure()
    for index, key in enumerate(metrics):
        figure.add_trace(
            go.Scatter(
                x=frame.month.dt.strftime("%Y-%m-%d").tolist(),
                y=frame[key].tolist(),
                name=LABELS[key],
                mode="lines+markers",
                line={"color": COLORS[index], "width": 3},
                marker={"size": 4},
                hovertemplate="%{x|%b %Y}<br>USD %{y:,.2f}<extra>%{fullData.name}</extra>",
            )
        )
    figure.update_layout(
        template="plotly_white",
        height=330,
        margin={"l": 12, "r": 12, "t": 15, "b": 10},
        legend={"orientation": "h", "y": 1.15, "x": 0},
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#23354d"},
        yaxis={"title": "USD", "tickprefix": "$", "gridcolor": "#e8edf4"},
        xaxis={"title": None, "type": "date", "tickformat": "%b %y", "showgrid": False},
    )
    if len(frame) > 1:
        figure.update_xaxes(
            range=[
                frame.month.min().strftime("%Y-%m-%d"),
                frame.month.max().strftime("%Y-%m-%d"),
            ]
        )
    return figure


def concentration_chart(frame, label_column):
    ordered = frame.sort_values("deposit_balance", ascending=True)
    figure = go.Figure(
        go.Bar(
            x=ordered.deposit_balance.tolist(),
            y=ordered[label_column].tolist(),
            orientation="h",
            marker_color=COLORS[0],
            customdata=ordered.deposit_share_percent.tolist(),
            hovertemplate="%{y}<br>Deposits: USD %{x:,.2f}<br>Share: %{customdata:.1f}%<extra></extra>",
        )
    )
    figure.update_layout(
        template="plotly_white",
        height=max(300, min(650, 80 + len(frame) * 27)),
        margin={"l": 12, "r": 12, "t": 10, "b": 10},
        xaxis={"title": "Closing deposits (USD)", "tickprefix": "$"},
        yaxis={"title": None},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure


def product_chart(penetration):
    figure = go.Figure(
        go.Bar(
            x=list(penetration.values()),
            y=[LABELS[key] for key in penetration],
            orientation="h",
            marker_color=COLORS[1],
            text=[f"{value:.1f}%" for value in penetration.values()],
            textposition="auto",
            hovertemplate="%{y}<br>%{x:.1f}% of selected customers<extra></extra>",
        )
    )
    figure.update_layout(
        template="plotly_white",
        height=310,
        margin={"l": 12, "r": 12, "t": 10, "b": 10},
        xaxis={"title": "Customer adoption (%)", "range": [0, 105]},
        yaxis={"title": None, "autorange": "reversed"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure


OPPORTUNITY_PRODUCTS = {
    "Deposit relationship": "Deposit relationship",
    "merchant_services": "Merchant services",
    "payroll_services": "Payroll services",
    "treasury_services": "Treasury services",
    "credit_card": "Credit card",
}


def signal_distribution_chart(frame, by):
    label = "rm_name" if by == "rm" else "product"
    ordered = frame.groupby(label).signal_count.sum().sort_values().index.tolist()
    labels = [OPPORTUNITY_PRODUCTS.get(value, value) for value in ordered]
    figure = go.Figure()
    for signal_type, color in [("Retention", "#c08b33"), ("Cross-sell", "#087f8c")]:
        counts = frame[frame.signal_type == signal_type].set_index(label).signal_count
        figure.add_trace(
            go.Bar(
                x=[int(counts.get(value, 0)) for value in ordered],
                y=labels,
                name=signal_type,
                orientation="h",
                marker_color=color,
                hovertemplate="%{y}<br>%{x} signals<extra>%{fullData.name}</extra>",
            )
        )
    figure.update_layout(
        template="plotly_white",
        barmode="stack",
        height=max(330, min(650, 100 + len(ordered) * 25)),
        margin={"l": 12, "r": 12, "t": 25, "b": 10},
        legend={"orientation": "h", "y": 1.13, "x": 0},
        xaxis={
            "title": "Signal count",
            "dtick": 1 if frame.signal_count.sum() < 20 else None,
        },
        yaxis={"title": None},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return figure
