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
            max-width: 1180px;
        }}
        div[data-testid="stHorizontalBlock"] {{
            align-items: stretch;
        }}
        div[data-testid="column"] {{
            min-width: 0;
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] div[data-testid="stVerticalBlockBorderWrapper"] {{
            height: 100%;
        }}
        .finn-decision-inline {{
            display: block;
            font-size: 0.95rem;
            font-weight: 600;
            margin: 0.35rem 0 0.65rem 0;
        }}
        .finn-decision-banner {{
            background: #fff;
            border: 1px solid #E8ECF0;
            border-left-width: 5px;
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin-bottom: 1rem;
        }}
        .finn-decision-banner-action {{
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            line-height: 1.2;
            margin-bottom: 0.35rem;
        }}
        .finn-decision-banner-meta {{
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.45;
        }}
        .finn-decision-banner-sep {{
            margin: 0 0.35rem;
            color: #CBD5E1;
        }}
        /* Decision hero — gauge + action panels equal height */
        .finn-decision-banner + div[data-testid="stHorizontalBlock"] {{
            align-items: stretch !important;
        }}
        .finn-decision-banner + div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
            display: flex;
            flex-direction: column;
        }}
        .finn-decision-banner + div[data-testid="stHorizontalBlock"] [data-testid="stVerticalBlockBorderWrapper"] {{
            flex: 1;
            min-height: 248px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .finn-decision-banner + div[data-testid="stHorizontalBlock"] [data-testid="stPlotlyChart"] {{
            margin-top: auto;
            margin-bottom: auto;
        }}
        .finn-action-headline {{
            font-size: 1.02rem;
            font-weight: 600;
            color: #0F172A;
            margin: 0 0 0.65rem 0;
            line-height: 1.45;
        }}
        .finn-action-meta {{
            font-size: 0.86rem;
            color: #64748B;
            margin: 0;
            line-height: 1.55;
        }}
        /* Snapshot metric row directly under hero */
        .finn-decision-banner + div[data-testid="stHorizontalBlock"] + div[data-testid="stHorizontalBlock"] {{
            margin-top: 0.35rem;
            margin-bottom: 0.85rem;
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] [data-testid="stMetric"] {{
            height: 100%;
            min-height: 4.5rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
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
            font-size: 0.75rem !important;
            line-height: 1.25 !important;
            white-space: normal !important;
            min-height: 2.4em;
        }}
        [data-testid="stMetricValue"] {{
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            overflow: visible !important;
            white-space: nowrap;
        }}
        .finn-band-pill {{
            display: inline-block;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 0.2rem 0.55rem;
            border: 1px solid;
            border-radius: 999px;
            margin: 0.2rem 0 0.55rem 0;
        }}
        .finn-event {{
            font-size: 0.84rem;
            line-height: 1.45;
            padding: 0.55rem 0.65rem;
            margin-bottom: 0.4rem;
            border-radius: 8px;
            border-left: 3px solid #E2E8F0;
            background: #F8FAFC;
            color: #334155;
        }}
        .finn-event-meta {{
            display: block;
            font-size: 0.72rem;
            font-weight: 600;
            color: #64748B;
            margin-bottom: 0.15rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .finn-event-negative {{ border-left-color: #EF4444; background: #FEF2F2; }}
        .finn-event-positive {{ border-left-color: #22C55E; background: #F0FDF4; }}
        .finn-event-neutral {{ border-left-color: #94A3B8; }}
        h1 {{ font-size: 1.65rem !important; font-weight: 600 !important; margin-bottom: 0.2rem !important; }}
        h2, h3 {{ font-size: 1.05rem !important; font-weight: 600 !important; }}
        [data-testid="stSidebar"] {{
            background-color: #FAFBFC;
            border-right: 1px solid #E8ECF0;
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
        .finn-upi-panel {{
            display: grid;
            grid-template-columns: 1.2fr 3fr;
            gap: 0.85rem;
            align-items: center;
            background: #fff;
            border: 1px solid #E8ECF0;
            border-radius: 12px;
            padding: 0.75rem 0.85rem;
            margin: 0.75rem 0 0.25rem 0;
        }}
        .finn-upi-title {{
            font-size: 0.92rem;
            font-weight: 600;
            color: #0F172A;
            margin-bottom: 0.15rem;
        }}
        .finn-upi-subtitle {{
            font-size: 0.76rem;
            color: #64748B;
            line-height: 1.35;
        }}
        .finn-upi-metrics {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.5rem;
            margin-top: 0;
        }}
        .finn-upi-metric {{
            background: #F8FAFC;
            border: 1px solid #E8ECF0;
            border-radius: 8px;
            padding: 0.5rem 0.6rem;
            min-width: 0;
        }}
        .finn-upi-metric .k {{
            display: block;
            font-size: 0.68rem;
            color: #64748B;
            margin-bottom: 0.1rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .finn-upi-metric .v {{
            display: block;
            font-size: 0.95rem;
            font-weight: 600;
            color: #0F172A;
            white-space: nowrap;
        }}
        @media (max-width: 900px) {{
            .finn-upi-panel {{
                grid-template-columns: 1fr;
            }}
            .finn-upi-metrics {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
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
