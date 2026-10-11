import streamlit as st

from streamlit_app.components import apply_style
from streamlit_app.views.portfolio_overview import render

st.set_page_config(
    page_title="Business Banking RM Intelligence Hub", page_icon="🏦", layout="wide"
)
apply_style()
with st.sidebar:
    st.caption("BUSINESS BANKING")
    st.title("RM Intelligence Hub")
    st.caption("Relationship intelligence")
    st.divider()
st.caption("SYNTHETIC DEMO · Entirely fictional businesses and financial measures")
page = st.navigation(
    [
        st.Page(
            render,
            title="Portfolio Overview",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(
            "views/customer_360.py",
            title="Customer 360",
            icon=":material/account_balance:",
            url_path="customer-360",
        ),
        st.Page(
            "views/rm_opportunities.py",
            title="RM Opportunities",
            icon=":material/lightbulb:",
            url_path="rm-opportunities",
        ),
    ],
    position="top",
)
page.run()
