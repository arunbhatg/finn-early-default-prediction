"""Evidence charts — plot-heavy view."""

import streamlit as st

from app.components.underwriter import render_evidence_dashboard
from app.views._helpers import require_case


def page_evidence():
    st.title("Evidence & Trends")
    st.caption("Visual proof of business activity — what underwriters use when financials are unavailable.")

    if not require_case():
        return

    profile = st.session_state.profile
    render_evidence_dashboard(profile)

    with st.expander("Google reviews & sentiment (secondary)"):
        google = profile["google"]
        st.metric("Rating", f"{google['rating']} ★", f"{google['review_count']} reviews")
        pos = sum(1 for r in google["reviews"] if r["sentiment"] == "positive")
        st.caption(f"{pos}/{len(google['reviews'])} positive (NLP)")

    with st.expander("Macro & sector context (secondary)"):
        macro = profile["macro"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Monsoon index", f"{macro.get('monsoon_index_pct', 100)}%")
        c2.metric("Region", macro.get("region_tier", "N/A"))
        inv = profile["investment"]
        c3.metric("CapEx (12M)", f"₹{inv['capex_lakhs_12m']}L")
