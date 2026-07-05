"""Early warning signals — full data export."""

import streamlit as st

from app.components.summary_sheet import render_summary_sheet
from app.components.underwriter import render_collection_charts, render_unstructured_signals
from app.views._helpers import require_case


def page_details():
    st.markdown("### Early warning signals")
    st.caption("Collection timing, bureau other-loan behaviour, unstructured text evidence, and exports.")

    if not require_case():
        return

    profile = st.session_state.profile
    features = st.session_state.features

    render_collection_charts(profile, features)
    render_unstructured_signals(profile, features)

    with st.expander("Full data summary & export", expanded=False):
        render_summary_sheet(
            st.session_state.profile,
            st.session_state.features,
            st.session_state.score_result,
            st.session_state.get("source_status"),
        )
