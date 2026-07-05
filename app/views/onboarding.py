"""Optional full onboarding + consent flow."""

import streamlit as st

from app.components.widgets import source_fetch_progress
from app.views._helpers import assess_msme, load_case
from src.connectors.base import load_profile
from src.connectors.sources import fetch_all_sources


def page_onboarding_flow():
    st.caption("Simulates PAN/GSTIN capture → consent → data fetch (production would use AA/GSTN APIs).")

    from pathlib import Path

    import pandas as pd

    from src.connectors.sources import ALL_CONNECTORS

    root = Path(__file__).resolve().parents[2]
    path = root / "data" / "synthetic" / "msme_master.csv"
    if not path.exists():
        st.warning("Run scripts/generate_data.py first.")
        return

    import pandas as pd
    from src.connectors.sources import ALL_CONNECTORS

    master = pd.read_csv(path)

    with st.form("onboard"):
        sector = st.selectbox("Sector", master["sector"].unique())
        state = st.selectbox("State", master["state"].unique())
        if st.form_submit_button("Fetch & score"):
            match = master[(master["sector"] == sector) & (master["state"] == state)]
            msme_id = match.iloc[0]["msme_id"] if not match.empty else "MSME001"
            profile = load_profile(msme_id)
            sources = list(ALL_CONNECTORS.keys())
            source_fetch_progress(sources[:5])
            fetch_all_sources(msme_id, sources)
            bundle = assess_msme(msme_id, profile, sources)
            st.session_state.msme_id = msme_id
            st.session_state.profile = profile
            st.session_state.features = bundle["features"]
            st.session_state.score_result = bundle["score_result"]
            st.session_state.fetched = True
            st.session_state.page = "② Credit Decision"
            st.rerun()
