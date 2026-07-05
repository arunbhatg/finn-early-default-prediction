"""Reusable Streamlit UI components."""

import plotly.graph_objects as go
import streamlit as st

from src.utils.helpers import score_to_grade


def render_score_gauge(score: float, grade: str = "") -> None:
    if not grade:
        grade = score_to_grade(score)
    color = "#22C55E" if score >= 650 else "#EAB308" if score >= 550 else "#EF4444"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "", "font": {"size": 36}},
            title={"text": grade, "font": {"size": 16}},
            gauge={
                "axis": {"range": [300, 900], "tickwidth": 0},
                "bar": {"color": color, "thickness": 0.22},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [300, 550], "color": "#F8FAFC"},
                    {"range": [550, 650], "color": "#F1F5F9"},
                    {"range": [650, 750], "color": "#ECFDF5"},
                    {"range": [750, 900], "color": "#DCFCE7"},
                ],
            },
        )
    )
    fig.update_layout(height=260, margin=dict(t=48, b=16, l=24, r=24))
    st.plotly_chart(fig, use_container_width=True)
