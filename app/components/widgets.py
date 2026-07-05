"""Reusable Streamlit UI components."""

import plotly.graph_objects as go
import streamlit as st

from src.utils.ui_text import FINN_SCORE_LABEL


def render_stress_gauge(stress_pct: float, band: str = "", color: str = "#22C55E", *, chart_key: str = "stress_gauge") -> None:
    if not band:
        if stress_pct >= 70:
            band, color = "Critical", "#991B1B"
        elif stress_pct >= 45:
            band, color = "High", "#C2410C"
        elif stress_pct >= 25:
            band, color = "Watch", "#854D0E"
        else:
            band, color = "Low", "#166534"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=stress_pct,
            number={"suffix": "%", "font": {"size": 36}},
            title={
                "text": f"{band}<br><span style='font-size:11px'>{FINN_SCORE_LABEL}</span>",
                "font": {"size": 14},
            },
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 0},
                "bar": {"color": color, "thickness": 0.22},
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
    fig.update_layout(height=260, margin=dict(t=48, b=16, l=24, r=24))
    st.plotly_chart(fig, width="stretch", key=chart_key)


def render_score_gauge(score: float, grade: str = "") -> None:
    """Legacy alias — score is stress probability 0–100."""
    render_stress_gauge(score, grade)
