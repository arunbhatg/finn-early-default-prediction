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
            min-width: 0;
            overflow: visible;
        }}
        [data-testid="stMetric"] label {{
            font-size: 0.78rem !important;
            white-space: nowrap;
        }}
        [data-testid="stMetricValue"] {{
            font-size: 1.2rem !important;
            font-weight: 600 !important;
            overflow: visible !important;
            white-space: nowrap;
        }}
        .finn-case-stats {{
            display: flex;
            gap: 0.75rem;
            margin: 0.5rem 0 0.75rem 0;
        }}
        .finn-case-stat {{
            flex: 1;
            background: #fff;
            border: 1px solid #E8ECF0;
            border-radius: 10px;
            padding: 0.55rem 0.65rem;
            min-width: 0;
        }}
        .finn-case-stat .label {{
            display: block;
            color: #64748B;
            font-size: 0.68rem;
            line-height: 1.2;
            margin-bottom: 0.15rem;
        }}
        .finn-case-stat .value {{
            display: block;
            color: #0F172A;
            font-size: 1.05rem;
            font-weight: 600;
            white-space: nowrap;
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
        .finn-app-header {{
            margin-bottom: 0.5rem;
            padding-bottom: 0.85rem;
            border-bottom: 1px solid #E8ECF0;
        }}
        .finn-app-title {{
            font-size: 1.35rem;
            font-weight: 700;
            color: #0F172A;
            letter-spacing: -0.02em;
            line-height: 1.25;
        }}
        .finn-app-tagline {{
            margin-top: 0.2rem;
            font-size: 0.82rem;
            color: #64748B;
        }}
        .finn-section-title {{
            font-size: 0.92rem;
            font-weight: 600;
            color: #0F172A;
            margin: 1.1rem 0 0.55rem 0;
            padding-bottom: 0.3rem;
            border-bottom: 1px solid #E8ECF0;
        }}
        .finn-section-title:first-of-type {{
            margin-top: 0.15rem;
        }}
        .finn-news-heading {{
            font-size: 1.05rem;
            font-weight: 600;
            color: #0F172A;
            margin: 1.5rem 0 0.75rem 0;
            padding-top: 1.25rem;
            border-top: 2px solid #E8ECF0;
        }}
        .finn-chart-card {{
            background: #fff;
            border: 1px solid #E8ECF0;
            border-radius: 12px;
            padding: 0.35rem 0.5rem 0.15rem 0.5rem;
            margin-bottom: 0.25rem;
            min-height: 300px;
        }}
        .finn-upi-metrics {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.45rem;
            margin-top: 0.5rem;
        }}
        .finn-upi-metric {{
            background: #F8FAFC;
            border: 1px solid #E8ECF0;
            border-radius: 8px;
            padding: 0.45rem 0.55rem;
        }}
        .finn-upi-metric .k {{
            display: block;
            font-size: 0.68rem;
            color: #64748B;
            margin-bottom: 0.1rem;
        }}
        .finn-upi-metric .v {{
            display: block;
            font-size: 0.92rem;
            font-weight: 600;
            color: #0F172A;
        }}
        .finn-news-list {{
            margin-top: 0.75rem;
        }}
        .finn-news-item {{
            padding: 0.55rem 0;
            border-bottom: 1px solid #F1F5F9;
            font-size: 0.84rem;
            color: #334155;
            line-height: 1.4;
        }}
        .finn-case-card {{
            padding: 0.15rem 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
