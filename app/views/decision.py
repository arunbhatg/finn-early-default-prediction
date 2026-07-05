"""Primary underwriter decision screen."""

import streamlit as st

from app.components.underwriter import (
    render_decision_header,
    render_driver_chart,
    render_key_metrics_row,
    render_risk_flags,
)
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
    render_key_metrics_row(features, profile)

    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        render_driver_chart(result.get("boosters", []), result.get("draggers", []))
    with c2:
        pillar_bar_chart(result["pillars"])

    st.divider()
    render_risk_flags(features, profile)

    # Nice-to-have at the bottom
    with st.expander("Detailed source summaries (secondary)"):
        for s in result.get("data_summary", []):
            st.markdown(f"**{s['source']}** — {s['headline']}")
            for h in s.get("highlights", [])[:2]:
                st.caption(f"· {h}")

    with st.expander("Pillar-level driver detail (secondary)"):
        for pillar, data in result["pillars"].items():
            st.markdown(f"**{pillar.title()}** — {data['score']:.0f}/100")
            for d in data["drivers"][:3]:
                st.caption(f"{d['factor']}: {d['value']} ({d['impact']:.0f} pts)")
