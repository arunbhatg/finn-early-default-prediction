"""Shared view helpers."""

import streamlit as st

from src.connectors.base import load_profile
from src.connectors.data_summary import build_data_pull_summary
from src.connectors.enrichment import enrich_profile_with_public_data
from src.connectors.sources import ALL_CONNECTORS
from src.features.feature_engineering import extract_features
from src.prediction.model import compute_stress_prediction, predict_at_observation


def assess_msme(msme_id: str, profile: dict, sources: list[str] | None = None) -> dict:
    sources = sources or list(ALL_CONNECTORS.keys())
    enriched, source_status = enrich_profile_with_public_data(profile)
    result = predict_at_observation(enriched)
    features = extract_features(enriched, observation_month=result.get("observation_month"))
    features["_stress_prob_display"] = result["stress_prob"]
    result["data_summary"] = build_data_pull_summary(enriched, sources)

    return {
        "features": features,
        "score_result": result,
        "profile": enriched,
        "source_status": source_status,
    }


def load_case(msme_id: str) -> None:
    profile = load_profile(msme_id)
    bundle = assess_msme(msme_id, profile)
    st.session_state.msme_id = msme_id
    st.session_state.profile = bundle["profile"]
    st.session_state.features = bundle["features"]
    st.session_state.score_result = bundle["score_result"]
    st.session_state.source_status = bundle["source_status"]
    st.session_state.fetched = True


def require_case() -> bool:
    if not st.session_state.fetched or not st.session_state.score_result:
        st.markdown("### No loan selected")
        st.caption("Choose a loan from **Portfolio** to view stress assessment.")
        if st.button("Go to Portfolio", type="primary"):
            st.session_state.page = "Portfolio"
            st.rerun()
        return False
    return True
