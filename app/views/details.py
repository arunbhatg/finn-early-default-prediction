"""Data details — tables and exports for power users."""

import streamlit as st

from app.components.summary_sheet import render_summary_sheet
from app.views._helpers import require_case


def page_details():
    st.markdown("### Case details")
    st.caption("Full data tables, source snapshots, and exports.")

    if not require_case():
        return

    render_summary_sheet(
        st.session_state.profile,
        st.session_state.features,
        st.session_state.score_result,
        st.session_state.get("source_status"),
    )
