"""Case selection — clean entry screen."""

import streamlit as st

from app.views._helpers import load_case
from src.connectors.base import load_profile
from src.features.feature_engineering import extract_features
from src.utils.constants import DEMO_PERSONAS
from src.utils.display_metrics import bill_pay_on_time_pct
from src.utils.labels import FINN_SCORE_LABEL


def _decision_color(action: str) -> str:
    return {"APPROVE": "#166534", "REVIEW": "#854D0E", "DECLINE": "#991B1B"}.get(action, "#64748B")


def page_cases():
    from src.scoring.model import compute_final_score
    from src.scoring.underwriter_insights import get_credit_decision

    st.markdown("### Select a case")
    st.caption("Choose a demo MSME profile to generate a FINN. alternative score.")

    cols = st.columns(2)
    for i, (msme_id, meta) in enumerate(DEMO_PERSONAS.items()):
        profile = load_profile(msme_id)
        features = extract_features(profile)
        score = int(compute_final_score(features)["final_score"])
        decision = get_credit_decision(score)["action"]

        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"##### {meta['name']}")
                st.caption(f"{meta['sector']} · {meta['city']}")
                turnover_l = features["gst_avg_monthly_turnover"]
                bill_on_time = bill_pay_on_time_pct(features)
                st.markdown(
                    f"""
                    <div class="finn-case-stats">
                        <div class="finn-case-stat">
                            <span class="label">{FINN_SCORE_LABEL}</span>
                            <span class="value">{score}</span>
                        </div>
                        <div class="finn-case-stat">
                            <span class="label">Turnover / mo</span>
                            <span class="value">Rs {turnover_l:.1f}L</span>
                        </div>
                        <div class="finn-case-stat">
                            <span class="label">Bill on-time</span>
                            <span class="value">{bill_on_time:.0f}%</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span class='finn-decision' style='color:{_decision_color(decision)}'>{decision}</span>",
                    unsafe_allow_html=True,
                )
                if st.button("Open case", key=f"open_{msme_id}", width="stretch", type="primary"):
                    load_case(msme_id)
                    st.session_state.page = "Assessment"
                    st.rerun()
