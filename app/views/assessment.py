"""Stress assessment — overview, charts, loan/collections tabs."""

import streamlit as st

from app.components.underwriter import render_charts, render_loan_panel, render_overview, render_unstructured_signals
from app.views._helpers import require_case


def page_assessment():
    if not require_case():
        return

    profile = st.session_state.profile
    features = st.session_state.features
    result = st.session_state.score_result
    loan_type = profile.get("loan_book", {}).get("loan_type", "—")
    obs = result.get("observation_month", "—")

    st.markdown(f"### {profile['business_name']}")
    st.caption(f"{loan_type} · {profile['city']} · observation month {obs} · 12-month horizon")

    tab1, tab2, tab3 = st.tabs(["Stress overview", "Collections & trends", "Unstructured signals"])

    with tab1:
        render_overview(profile, features, result)

    with tab2:
        render_charts(profile, features)

    with tab3:
        render_unstructured_signals(profile, features)
        render_loan_panel(profile, features)
