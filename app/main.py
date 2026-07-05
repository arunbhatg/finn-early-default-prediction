"""Streamlit entry — clean 3-step underwriter flow."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.components.branding import render_footer_branding, render_sidebar_branding, render_sidebar_footer_link
from app.components.styles import inject_styles
from app.views.assessment import page_assessment
from app.views.cases import page_cases
from app.views.details import page_details

PAGES = {
    "Cases": page_cases,
    "Assessment": page_assessment,
    "Details": page_details,
}


def init_session():
    defaults = {
        "page": "Cases",
        "msme_id": None,
        "profile": None,
        "features": None,
        "score_result": None,
        "source_status": None,
        "fetched": False,
        "_bootstrapped": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def bootstrap_once():
    if st.session_state._bootstrapped:
        return
    with st.spinner("Starting…"):
        from src.bootstrap import ensure_ready
        ensure_ready()
    st.session_state._bootstrapped = True


def sidebar():
    render_sidebar_branding()

    if st.session_state.fetched and st.session_state.profile:
        p = st.session_state.profile
        score = int(st.session_state.score_result["final_score"]) if st.session_state.score_result else "—"
        st.sidebar.markdown(
            f"**{p['business_name'][:26]}**  \n"
            f"<span class='finn-muted'>{p['sector']} · {score}</span>",
            unsafe_allow_html=True,
        )
        if st.sidebar.button("Change case", use_container_width=True):
            st.session_state.page = "Cases"
            st.rerun()
    else:
        st.sidebar.caption("Pick a case to begin")

    render_sidebar_footer_link()


def top_nav():
    labels = list(PAGES.keys())
    has_case = st.session_state.fetched and st.session_state.score_result
    if not has_case:
        labels = ["Cases"]

    idx = labels.index(st.session_state.page) if st.session_state.page in labels else 0
    st.markdown('<div class="finn-nav">', unsafe_allow_html=True)
    page = st.radio(
        "Navigate",
        labels,
        index=idx,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if page != st.session_state.page:
        st.session_state.page = page
        st.rerun()


def run_app():
    st.set_page_config(
        page_title="FinHealth Card | FINN.",
        page_icon="🟢",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_styles()
    init_session()
    bootstrap_once()
    sidebar()
    top_nav()
    PAGES[st.session_state.page]()
    render_footer_branding()


run_app()
