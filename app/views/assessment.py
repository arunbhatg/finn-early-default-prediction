"""Unified assessment — overview, charts, loan in tabs."""

import streamlit as st

from app.components.underwriter import render_charts, render_loan_panel, render_overview
from app.views._helpers import require_case


def page_assessment():
    if not require_case():
        return

    profile = st.session_state.profile
    features = st.session_state.features
    result = st.session_state.score_result

    st.title(profile["business_name"])
    st.caption(f"{profile['sector']} · {profile['city']} · {profile['gstin']}")

    tab1, tab2, tab3 = st.tabs(["Overview", "Charts", "Loan"])

    with tab1:
        render_overview(profile, features, result)

    with tab2:
        render_charts(profile, features)

    with tab3:
        render_loan_panel(features, result)
