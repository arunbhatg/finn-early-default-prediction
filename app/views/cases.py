"""Demo case selection — entry point for underwriters."""

import streamlit as st

from app.components.underwriter import render_demo_card
from app.views._helpers import load_case
from src.connectors.base import load_profile
from src.features.feature_engineering import extract_features
from src.scoring.model import compute_final_score
from src.scoring.underwriter_insights import get_demo_preview
from src.utils.constants import DEMO_PERSONAS


def page_select_case():
    st.title("Select MSME Case")
    st.caption("Choose a demo borrower — each case shows how alt-data supports NTC underwriting decisions.")

    st.markdown(
        """
        | Case | What it demonstrates |
        |------|---------------------|
        | **MSME001** | Credit-invisible manufacturer approved on GST + payroll + promoter quality |
        | **MSME002** | Retail kirana with no formal books but strong UPI + customer sentiment |
        | **MSME003** | Same business rejected on compliance, litigation, and bureau weakness |
        | **MSME004** | Agri dealer with sector/macro overlay improving risk view |
        """
    )

    cols = st.columns(2)
    for i, (msme_id, meta) in enumerate(DEMO_PERSONAS.items()):
        profile = load_profile(msme_id)
        features = extract_features(profile)
        score = compute_final_score(features)["final_score"]
        preview = get_demo_preview(msme_id, features, profile, score)

        with cols[i % 2]:
            if render_demo_card(preview, meta, f"case_{msme_id}"):
                load_case(msme_id)
                st.session_state.page = "② Credit Decision"
                st.rerun()

    st.divider()
    st.caption("Tip: Compare MSME001 (approve) vs MSME003 (decline) to show NTC underwriting value.")
