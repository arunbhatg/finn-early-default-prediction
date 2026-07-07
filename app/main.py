"""Streamlit entry — portfolio early-warning flow."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.utils.ui_text import APP_BUILD, APP_TAGLINE, APP_TITLE, BRAND_NAME, FINN_SCORE_LABEL

PAGE_ORDER = ("Portfolio", "Decision", "Evidence")


def _run_page(name: str) -> None:
    if name == "Portfolio":
        from app.views.cases import page_cases

        page_cases()
    elif name == "Decision":
        from app.views.assessment import page_assessment

        page_assessment()
    elif name == "Evidence":
        from app.views.details import page_details

        page_details()


def init_session():
    defaults = {
        "page": "Portfolio",
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
    legacy_pages = {"Assessment": "Decision", "Signals": "Evidence"}
    if st.session_state.page in legacy_pages:
        st.session_state.page = legacy_pages[st.session_state.page]


def bootstrap_once():
    if st.session_state._bootstrapped:
        return
    with st.spinner("Starting…"):
        from src.bootstrap import ensure_ready

        ensure_ready()
    st.session_state._bootstrapped = True


def _sidebar_branding() -> None:
    try:
        from app.components.branding import render_sidebar_branding

        render_sidebar_branding()
    except Exception:
        st.sidebar.markdown(
            f'<span style="font-weight:700;font-size:1.2rem">{BRAND_NAME}'
            '<span style="color:#22C55E">.</span></span>',
            unsafe_allow_html=True,
        )
        st.sidebar.caption("Early Default Prediction")


def _sidebar_footer_link() -> None:
    try:
        from app.components.branding import render_sidebar_footer_link

        render_sidebar_footer_link()
    except Exception:
        st.sidebar.markdown("---")
        st.sidebar.caption("[Try Finndot AI app](https://play.google.com/store/apps/details?id=com.anomapro.finndot.prd)")


def sidebar():
    _sidebar_branding()

    if st.session_state.fetched and st.session_state.profile:
        p = st.session_state.profile
        prob = int(st.session_state.score_result["stress_prob"] * 100) if st.session_state.score_result else "—"
        loan_type = p.get("loan_book", {}).get("loan_type", "—")
        st.sidebar.markdown(
            f"**{p['business_name'][:26]}**  \n"
            f"<span class='finn-muted'>{loan_type} · {FINN_SCORE_LABEL}: {prob}%</span>",
            unsafe_allow_html=True,
        )
        if st.sidebar.button("Change case", width="stretch"):
            st.session_state.page = "Portfolio"
            st.rerun()
    else:
        st.sidebar.caption("Pick a loan from portfolio to begin")

    st.sidebar.caption(f"Build: {APP_BUILD}")
    _sidebar_footer_link()


def top_nav():
    labels = list(PAGE_ORDER) if st.session_state.fetched and st.session_state.score_result else ["Portfolio"]

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


def app_header():
    st.markdown(
        f"""
        <div class="finn-app-header">
            <div class="finn-app-title">{APP_TITLE}</div>
            <div class="finn-app-tagline">{APP_TAGLINE}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _footer_branding() -> None:
    try:
        from app.components.branding import render_footer_branding

        render_footer_branding()
    except Exception:
        st.markdown(
            '<div style="margin-top:2rem;padding-top:1rem;border-top:1px solid #E2E8F0;'
            f'text-align:center;font-size:0.78rem;color:#94A3B8;">Powered by {BRAND_NAME}.</div>',
            unsafe_allow_html=True,
        )


def run_app():
    from app.components.styles import inject_styles

    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🟢",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_styles()
    init_session()
    bootstrap_once()
    sidebar()
    app_header()
    top_nav()
    _run_page(st.session_state.page)
    _footer_branding()


if __name__ == "__main__":
    run_app()
