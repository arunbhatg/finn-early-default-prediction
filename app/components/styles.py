"""Global UI styles — clean, minimal layout."""

import streamlit as st

FINN_GREEN = "#22C55E"


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        #MainMenu, footer, header {{ visibility: hidden; }}
        .block-container {{
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 1040px;
        }}
        h1 {{ font-size: 1.65rem !important; font-weight: 600 !important; margin-bottom: 0.2rem !important; }}
        h2, h3 {{ font-size: 1.05rem !important; font-weight: 600 !important; }}
        [data-testid="stSidebar"] {{
            background-color: #FAFBFC;
            border-right: 1px solid #E8ECF0;
        }}
        [data-testid="stMetric"] {{
            background: #fff;
            border: 1px solid #E8ECF0;
            border-radius: 10px;
            padding: 0.6rem 0.7rem;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 12px;
            border-color: #E8ECF0 !important;
        }}
        [data-testid="stTabs"] button {{
            font-weight: 500;
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] .stButton > button {{
            border-radius: 8px;
        }}
        .finn-nav {{
            margin-bottom: 1.25rem;
        }}
        .finn-chip {{
            display: inline-block;
            padding: 0.3rem 0.6rem;
            margin: 0.12rem 0.2rem 0.12rem 0;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 500;
        }}
        .finn-chip-green {{ background: #DCFCE7; color: #166534; }}
        .finn-chip-red {{ background: #FEE2E2; color: #991B1B; }}
        .finn-chip-amber {{ background: #FEF9C3; color: #854D0E; }}
        .finn-decision {{
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}
        .finn-muted {{ color: #64748B; font-size: 0.85rem; }}
        .finn-case-card {{
            padding: 0.15rem 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
