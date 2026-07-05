"""Portfolio case selection."""

import streamlit as st

from app.views._helpers import load_case
from src.connectors.base import load_profile
from src.prediction.model import predict_at_observation
from src.utils.constants import DEMO_PERSONAS
from src.utils.ui_text import FINN_SCORE_LABEL


def _band_color(band: str) -> str:
    return {"Critical": "#991B1B", "High": "#C2410C", "Watch": "#854D0E", "Low": "#166534"}.get(band, "#64748B")


def page_cases():
    st.markdown("### MSME loan portfolio")
    st.caption("Select an active loan to view 12-month stress early-warning assessment.")

    cols = st.columns(2)
    for i, (msme_id, meta) in enumerate(DEMO_PERSONAS.items()):
        profile = load_profile(msme_id)
        result = predict_at_observation(profile)
        prob = int(result["stress_prob"] * 100)
        band = result["band"]
        loan_type = profile.get("loan_book", {}).get("loan_type", "—")
        is_ntc = profile.get("bureau", {}).get("is_ntc", False)
        credit_tag = "NTC" if is_ntc else "Bureau"

        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"##### {meta['name']}")
                st.caption(f"{loan_type} · {meta['city']} · {credit_tag}")
                st.markdown(
                    f"""
                    <div class="finn-case-stats">
                        <div class="finn-case-stat">
                            <span class="label">{FINN_SCORE_LABEL}</span>
                            <span class="value">{prob}%</span>
                        </div>
                        <div class="finn-case-stat">
                            <span class="label">Risk band</span>
                            <span class="value">{band}</span>
                        </div>
                        <div class="finn-case-stat">
                            <span class="label">Outstanding</span>
                            <span class="value">Rs {profile['loan_book']['outstanding_lakhs']:.1f}L</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span class='finn-decision' style='color:{_band_color(band)}'>{band.upper()}</span>",
                    unsafe_allow_html=True,
                )
                if st.button("Open assessment", key=f"open_{msme_id}", width="stretch", type="primary"):
                    load_case(msme_id)
                    st.session_state.page = "Assessment"
                    st.rerun()
