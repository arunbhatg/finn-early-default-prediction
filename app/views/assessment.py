"""Stress assessment — underwriter-first tabs."""

import streamlit as st

from app.components.underwriter import (
    render_alt_data_charts,
    render_collection_charts,
    render_loan_panel,
    render_overview,
    render_unstructured_signals,
)
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

    tab1, tab2, tab3 = st.tabs(["Decision", "Collections & Bureau", "Alt-data & Text"])
    case_key = profile.get("msme_id", "case")

    with tab1:
        render_overview(profile, features, result)

    with tab2:
        render_loan_panel(profile, features)
        render_collection_charts(profile, features, key_prefix=f"assess_coll_{case_key}")

    with tab3:
        render_alt_data_charts(profile, features, key_prefix=f"assess_alt_{case_key}")
        render_unstructured_signals(profile, features, key_prefix=f"assess_nlp_{case_key}")
