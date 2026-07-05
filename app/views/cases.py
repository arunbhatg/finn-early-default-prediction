"""Case selection — clean entry screen."""

import streamlit as st

from app.views._helpers import load_case
from src.connectors.base import load_profile
from src.features.feature_engineering import extract_features
from src.scoring.model import compute_final_score
from src.scoring.underwriter_insights import get_credit_decision, get_demo_preview
from src.utils.constants import DEMO_PERSONAS


def _decision_color(action: str) -> str:
    return {"APPROVE": "#166534", "REVIEW": "#854D0E", "DECLINE": "#991B1B"}.get(action, "#64748B")


def page_cases():
    st.title("Cases")
    st.caption("Open a demo MSME to run the financial health assessment.")

    cols = st.columns(2)
    for i, (msme_id, meta) in enumerate(DEMO_PERSONAS.items()):
        profile = load_profile(msme_id)
        features = extract_features(profile)
        score = int(compute_final_score(features)["final_score"])
        decision = get_credit_decision(score)["action"]
        preview = get_demo_preview(msme_id, features, profile, score)

        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f'<div class="finn-case-card">', unsafe_allow_html=True)
                st.markdown(f"##### {meta['name']}")
                st.caption(f"{meta['sector']} · {meta['city']}")
                c1, c2 = st.columns(2)
                c1.metric("Score", score)
                c2.metric("Turnover", preview["turnover"])
                st.markdown(
                    f"<span class='finn-decision' style='color:{_decision_color(decision)}'>{decision}</span>",
                    unsafe_allow_html=True,
                )
                if st.button("Open case", key=f"open_{msme_id}", use_container_width=True, type="primary"):
                    load_case(msme_id)
                    st.session_state.page = "Assessment"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
