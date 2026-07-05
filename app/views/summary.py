"""Full data summary sheet — all actual values."""

import streamlit as st

from app.components.summary_sheet import render_summary_sheet
from app.views._helpers import require_case


def page_summary_sheet():
    st.title("Data Summary Sheet")
    st.caption("Credit memo view — borrower identity, features, scores, and source-level actuals.")

    if not require_case():
        return

    render_summary_sheet(
        st.session_state.profile,
        st.session_state.features,
        st.session_state.score_result,
        st.session_state.get("source_status"),
    )
