"""Shared view helpers."""

import streamlit as st

from src.connectors.base import load_profile
from src.connectors.data_summary import build_data_pull_summary
from src.connectors.enrichment import enrich_profile_with_public_data
from src.connectors.sources import ALL_CONNECTORS
from src.features.feature_engineering import extract_features
from src.scoring.explainability import build_score_narrative, extract_score_drivers
from src.scoring.model import compute_final_score


def assess_msme(msme_id: str, profile: dict, sources: list[str] | None = None) -> dict:
    sources = sources or list(ALL_CONNECTORS.keys())
    enriched, source_status = enrich_profile_with_public_data(profile)
    features = extract_features(enriched)
    result = compute_final_score(features)

    drivers = extract_score_drivers(result["pillars"])
    result["boosters"] = drivers["boosters"]
    result["draggers"] = drivers["draggers"]
    result["narrative"] = build_score_narrative(
        result["final_score"], drivers["boosters"], drivers["draggers"]
    )
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
        st.warning("Select an MSME case first (① Select MSME Case).")
        if st.button("Go to case selection"):
            st.session_state.page = "① Select MSME Case"
            st.rerun()
        return False
    return True
