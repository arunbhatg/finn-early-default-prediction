"""Streamlit entry — underwriter workflow for FinHealth Card."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.components.branding import render_footer_branding, render_sidebar_branding, render_sidebar_footer_link
from app.views.cases import page_select_case
from app.views.decision import page_credit_decision
from app.views.evidence import page_evidence
from app.views.loan import page_loan_offer
from app.views.onboarding import page_onboarding_flow
from app.views.summary import page_summary_sheet

NAV = {
    "① Select MSME Case": page_select_case,
    "② Credit Decision": page_credit_decision,
    "③ Evidence & Trends": page_evidence,
    "④ Loan Offer": page_loan_offer,
    "⑤ Data Summary Sheet": page_summary_sheet,
}


def init_session():
    defaults = {
        "page": "① Select MSME Case",
        "msme_id": None,
        "profile": None,
        "features": None,
        "score_result": None,
        "fetched": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def sidebar():
    render_sidebar_branding()

    if st.session_state.msme_id and st.session_state.profile:
        st.sidebar.success(st.session_state.profile.get("business_name", ""))
        st.sidebar.caption(f"{st.session_state.msme_id} · {st.session_state.profile.get('sector', '')}")
        if st.session_state.score_result:
            st.sidebar.metric("Health Score", int(st.session_state.score_result["final_score"]))
        if st.session_state.get("source_status"):
            live_n = sum(1 for s in st.session_state.source_status if s["mode"] == "live")
            st.sidebar.caption(f"Data: {live_n} live connector(s)")
    else:
        st.sidebar.info("Select a demo case to begin")

    st.sidebar.divider()
    st.sidebar.markdown("**Workflow**")
    page = st.sidebar.radio("Go to", list(NAV.keys()), index=list(NAV.keys()).index(st.session_state.page))
    st.session_state.page = page

    st.sidebar.divider()
    with st.sidebar.expander("Full onboarding flow (optional)"):
        page_onboarding_flow()

    render_sidebar_footer_link()


def run_app():
    st.set_page_config(
        page_title="FinHealth Card | FINN.",
        page_icon="🟢",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.spinner("Loading FinHealth Card..."):
        from src.bootstrap import ensure_ready
        ensure_ready()

    init_session()
    sidebar()
    NAV[st.session_state.page]()
    render_footer_branding()


run_app()
