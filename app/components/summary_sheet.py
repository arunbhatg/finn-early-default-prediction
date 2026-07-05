"""Summary tables — simplified for Details page."""

import streamlit as st

from src.scoring.summary_data import (
    borrower_identity_table,
    features_table,
    score_summary_table,
    source_snapshot_tables,
)


def render_summary_sheet(profile, features, result, source_status=None):
    tab1, tab2, tab3 = st.tabs(["Borrower & stress", "By source", "Connectors"])

    with tab1:
        st.dataframe(borrower_identity_table(profile), width="stretch", hide_index=True)
        st.dataframe(score_summary_table(result), width="stretch", hide_index=True)
        st.download_button(
            "Download features CSV",
            features_table(features).to_csv(index=False),
            f"{profile['msme_id']}_features.csv",
        )

    with tab2:
        tables = source_snapshot_tables(profile)
        source = st.selectbox("Source", list(tables.keys()), label_visibility="collapsed")
        st.dataframe(tables[source], width="stretch", hide_index=True)

    with tab3:
        if source_status:
            for s in source_status:
                badge = {"live": "🟢", "static": "🟡", "mock": "⚪"}.get(s["mode"], "⚪")
                st.caption(f"{badge} **{s['name']}** — {s['detail']}")
        else:
            st.caption("No connector metadata.")
