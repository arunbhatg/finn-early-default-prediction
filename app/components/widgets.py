"""Reusable Streamlit UI components."""

import plotly.graph_objects as go
import streamlit as st

from src.utils.ui_text import FINN_SCORE_LABEL


def render_stress_gauge(
    stress_pct: float,
    band: str = "",
    color: str = "#22C55E",
    *,
    chart_key: str = "stress_gauge",
    compact: bool = False,
) -> None:
    if not band:
        if stress_pct >= 70:
            band, color = "Critical", "#991B1B"
        elif stress_pct >= 45:
            band, color = "High", "#C2410C"
        elif stress_pct >= 25:
            band, color = "Watch", "#854D0E"
        else:
            band, color = "Low", "#166534"

    title_font = 12 if compact else 14
    number_font = 32 if compact else 36
    chart_height = 196 if compact else 220
    top_margin = 32 if compact else 40

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=stress_pct,
            number={"suffix": "%", "font": {"size": number_font}},
            title={
                "text": f"{band}<br><span style='font-size:10px'>{FINN_SCORE_LABEL}</span>",
                "font": {"size": title_font},
            },
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 0, "visible": not compact},
                "bar": {"color": color, "thickness": 0.24},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 25], "color": "#ECFDF5"},
                    {"range": [25, 45], "color": "#FEF9C3"},
                    {"range": [45, 70], "color": "#FFEDD5"},
                    {"range": [70, 100], "color": "#FEE2E2"},
                ],
            },
        )
    )
    fig.update_layout(
        height=chart_height,
        margin=dict(t=top_margin, b=0, l=8, r=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width="stretch", key=chart_key)


def render_score_gauge(score: float, grade: str = "") -> None:
    """Legacy alias — score is stress probability 0–100."""
    render_stress_gauge(score, grade)
