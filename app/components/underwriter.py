"""Underwriter-focused UI panels."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

from app.components.widgets import pillar_bar_chart, render_score_gauge
from src.scoring.underwriter_insights import get_credit_decision, get_key_metrics, get_risk_flags, get_traditional_gap


def render_decision_header(score: float, grade: str, profile: dict, features: dict) -> None:
    decision = get_credit_decision(score)
    c1, c2, c3 = st.columns([1.2, 1, 1])

    with c1:
        render_score_gauge(score, grade)

    with c2:
        st.markdown("### Credit recommendation")
        color_map = {"green": "green", "orange": "orange", "red": "red"}
        color = color_map[decision["color"]]
        st.markdown(f":{color}[**{decision['action']}**]")
        st.caption(decision["headline"])
        st.write(decision["rationale"])
        st.markdown(f"**{profile['business_name']}**")
        st.caption(f"{profile['sector']} · {profile['city']} · GSTIN {profile['gstin']}")

    with c3:
        gap = get_traditional_gap(profile, score)
        st.markdown("### Traditional vs Alt-data")
        st.error(f"**{gap['traditional']}**  \n{gap['traditional_reason']}")
        st.success(f"**{gap['alt_data']}**  \n{gap['alt_reason']}")
        st.caption(f"{gap['sources_used']} sources · Decision in {gap['time_to_decision']}")


def render_key_metrics_row(features: dict, profile: dict) -> None:
    st.markdown("#### Key underwriting metrics")
    metrics = get_key_metrics(features, profile)
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.metric(m["label"], m["value"], help=f"Benchmark: {m['benchmark']}")


def render_risk_flags(features: dict, profile: dict) -> None:
    flags = get_risk_flags(features, profile)
    if not flags:
        return

    st.markdown("#### Risk & strength flags")
    reds = [f for f in flags if f["level"] == "red"]
    ambers = [f for f in flags if f["level"] == "amber"]
    greens = [f for f in flags if f["level"] == "green"]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Concerns**")
        for f in reds:
            st.error(f"**{f['label']}** — {f['detail']}")
        for f in ambers:
            st.warning(f"**{f['label']}** — {f['detail']}")
        if not reds and not ambers:
            st.caption("No material concerns flagged")
    with c2:
        st.markdown("**Strengths**")
        for f in greens:
            st.success(f"**{f['label']}** — {f['detail']}")
    with c3:
        st.markdown("**Pillar scores**")
        # placeholder — filled by caller if pillars passed


def render_driver_chart(boosters: list, draggers: list) -> None:
    rows = boosters[:4] + draggers[:4]
    if not rows:
        return
    df = pd.DataFrame({
        "factor": [r["factor"][:30] for r in rows],
        "points": [r["score_points"] for r in rows],
        "type": ["Boost" if r["score_points"] > 0 else "Drag" for r in rows],
    })
    fig = px.bar(
        df, x="points", y="factor", orientation="h", color="type",
        color_discrete_map={"Boost": "#22C55E", "Drag": "#EF4444"},
        title="Score drivers (approx. points)",
    )
    fig.update_layout(height=300, showlegend=False, margin=dict(t=40, l=10))
    st.plotly_chart(fig, use_container_width=True)


def render_evidence_dashboard(profile: dict) -> None:
    """Plot-heavy evidence view for underwriters."""
    gst = profile["gst"]
    upi = profile["upi"]
    aa = profile["aa"]
    epfo = profile["epfo"]

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        df = pd.DataFrame({"Turnover (₹L)": gst["monthly_turnover_lakhs"]})
        df.index = [f"M{i+1}" for i in range(len(df))]
        st.plotly_chart(px.line(df, markers=True, title="GST turnover trend"), use_container_width=True)
    with r1c2:
        df = pd.DataFrame({"UPI volume (₹L)": upi["monthly_volume_lakhs"]})
        df.index = [f"M{i+1}" for i in range(len(df))]
        st.plotly_chart(px.bar(df, title="UPI collections"), use_container_width=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        df = pd.DataFrame({
            "Credits": aa["monthly_credits_lakhs"],
            "Debits": aa["monthly_debits_lakhs"],
        })
        df.index = [f"M{i+1}" for i in range(len(df))]
        st.plotly_chart(px.area(df, title="Bank cash flow (AA)"), use_container_width=True)
    with r2c2:
        df = pd.DataFrame({
            "Headcount": epfo["employee_count"],
            "Wage bill (₹L)": epfo["monthly_wage_bill_lakhs"],
        })
        df.index = [f"M{i+1}" for i in range(len(df))]
        st.plotly_chart(px.line(df, markers=True, title="Payroll (EPFO)"), use_container_width=True)


def render_demo_card(preview: dict, meta: dict, button_key: str) -> bool:
    """Render a demo case card; returns True if selected."""
    with st.container(border=True):
        st.markdown(f"**{meta['name']}**")
        st.caption(f"{preview['type']} · {meta['city']}, {meta['state']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Score", preview["score"])
        c2.metric("Decision", preview["decision"])
        c3.metric("Turnover", preview["turnover"])
        c4.metric("CIBIL", preview["cibil"])
        st.caption(
            f"GST {preview['gst_compliance']} · Litigation {preview['litigation']} · _{preview['tag']}_"
        )
        return st.button(f"Open case →", key=button_key, use_container_width=True)
