"""Supporting evidence — collections, digital signals, text, export."""

import streamlit as st

from app.components.summary_sheet import render_summary_sheet
from app.components.underwriter import (
    render_alt_data_charts,
    render_collection_charts,
    render_evidence_summary,
    render_loan_panel,
    render_unstructured_signals,
)
from app.views._helpers import require_case


def page_details():
    st.markdown("### Supporting evidence")
    st.caption("Full audit trail — payments, bureau, GST/UPI/banking trends, and text-derived signals.")

    if not require_case():
        return

    profile = st.session_state.profile
    features = st.session_state.features
    result = st.session_state.score_result
    case_key = profile.get("msme_id", "case")

    render_evidence_summary(profile, features, result)

    st.markdown("#### Facility & payments")
    render_loan_panel(profile, features)
    render_collection_charts(profile, features, key_prefix=f"signals_coll_{case_key}")

    st.markdown("#### Business & digital footprint")
    render_alt_data_charts(profile, features, key_prefix=f"signals_alt_{case_key}")

    render_unstructured_signals(profile, features, key_prefix=f"signals_nlp_{case_key}")

    with st.expander("Full data summary & export", expanded=False):
        render_summary_sheet(
            st.session_state.profile,
            st.session_state.features,
            st.session_state.score_result,
            st.session_state.get("source_status"),
        )
