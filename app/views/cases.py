"""Portfolio case selection — sorted by stress, action-first."""

import streamlit as st

from app.views._helpers import load_case
from src.connectors.base import load_profile
from src.prediction.model import predict_at_observation
from src.prediction.stress_insights import get_stress_decision
from src.utils.constants import DEMO_PERSONAS
from src.utils.display_helpers import describe_month_on_book


def _load_cases() -> list[tuple]:
    cases = []
    for msme_id, meta in DEMO_PERSONAS.items():
        profile = load_profile(msme_id)
        result = predict_at_observation(profile)
        cases.append((result["stress_prob"], msme_id, meta, profile, result))
    cases.sort(key=lambda x: x[0], reverse=True)
    return cases


def page_cases():
    st.markdown("### MSME loan portfolio")
    st.caption("Ranked by 12-month stress risk — highest first.")

    cols = st.columns(2, gap="medium")
    for i, (prob_f, msme_id, meta, profile, result) in enumerate(_load_cases()):
        prob = int(prob_f * 100)
        band = result["band"]
        decision = result.get("decision") or get_stress_decision(prob_f)
        loan_type = profile.get("loan_book", {}).get("loan_type", "—")
        outstanding = profile["loan_book"]["outstanding_lakhs"]
        mob = describe_month_on_book(profile, result.get("observation_month"))["short"]

        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"##### {meta['name']}")
                st.caption(f"{loan_type} · {meta['city']} · {mob}")

                m1, m2, m3 = st.columns(3, gap="small")
                m1.metric("Stress risk", f"{prob}%")
                m2.metric("Action", decision["action"])
                m3.metric("Outstanding", f"₹{outstanding:.1f}L")

                st.markdown(
                    f"<span class='finn-band-pill' style='border-color:{decision['color']};color:{decision['color']}'>"
                    f"{band}</span>",
                    unsafe_allow_html=True,
                )
                if st.button("Review decision", key=f"open_{msme_id}", width="stretch", type="primary"):
                    load_case(msme_id)
                    st.session_state.page = "Decision"
                    st.rerun()
