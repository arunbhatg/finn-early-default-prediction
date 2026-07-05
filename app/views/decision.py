"""Primary underwriter decision screen."""

import streamlit as st

from app.components.summary_sheet import (
    render_flags_with_detail,
    render_metric_row_with_drilldown,
    render_source_status,
    render_summary_sheet,
)
from app.components.underwriter import render_decision_header, render_driver_chart
from app.components.widgets import pillar_bar_chart
from app.views._helpers import require_case
from src.utils.helpers import score_to_grade


def page_credit_decision():
    st.title("Credit Decision")
    if not require_case():
        return

    profile = st.session_state.profile
    features = st.session_state.features
    result = st.session_state.score_result
    score = result["final_score"]
    grade = score_to_grade(score)

    render_decision_header(score, grade, profile, features)
    st.divider()
    render_metric_row_with_drilldown(features, profile)

    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        render_driver_chart(result.get("boosters", []), result.get("draggers", []))
    with c2:
        pillar_bar_chart(result["pillars"])

    st.divider()
    render_flags_with_detail(features, profile)

    if st.session_state.get("source_status"):
        st.divider()
        with st.expander("🔌 Data connector status (live vs mock)", expanded=False):
            render_source_status(st.session_state.source_status)

    st.divider()
    with st.expander("📋 Quick summary sheet (click to expand)", expanded=False):
        render_summary_sheet(
            profile, features, result, st.session_state.get("source_status")
        )

    if st.button("Open full summary sheet →", type="primary"):
        st.session_state.page = "⑤ Data Summary Sheet"
        st.rerun()
