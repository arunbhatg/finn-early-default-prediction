"""Clean underwriter UI — minimal clutter."""

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.widgets import render_score_gauge
from src.scoring.loan_simulator import simulate_loan
from src.scoring.underwriter_insights import get_credit_decision, get_key_metrics, get_risk_flags
from src.utils.constants import SECTOR_GROWTH


def _chips(flags: list[dict], levels: tuple[str, ...], css: str, limit: int = 4) -> None:
    items = [f for f in flags if f["level"] in levels][:limit]
    if not items:
        st.caption("—")
        return
    html = "".join(
        f"<span class='finn-chip {css}'>{f['label']}</span>" for f in items
    )
    st.markdown(html, unsafe_allow_html=True)


def render_overview(profile: dict, features: dict, result: dict) -> None:
    from src.utils.helpers import score_to_grade

    score = result["final_score"]
    grade = score_to_grade(score)
    decision = get_credit_decision(score)

    left, right = st.columns([1.1, 1])
    with left:
        render_score_gauge(score, grade)
    with right:
        color = {"green": "#166534", "orange": "#854D0E", "red": "#991B1B"}[decision["color"]]
        st.markdown(
            f"<p class='finn-decision' style='color:{color};margin-bottom:0.25rem'>{decision['action']}</p>"
            f"<p class='finn-muted'>{decision['headline']}</p>",
            unsafe_allow_html=True,
        )

    metrics = get_key_metrics(features, profile)
    cols = st.columns(4)
    for i, m in enumerate(metrics):
        with cols[i % 4]:
            st.metric(m["label"], m["value"])

    flags = get_risk_flags(features, profile)
    if flags:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Concerns**")
            _chips(flags, ("red", "amber"), "finn-chip-red")
        with c2:
            st.markdown("**Strengths**")
            _chips(flags, ("green",), "finn-chip-green")

    boosters = result.get("boosters", [])[:3]
    draggers = result.get("draggers", [])[:3]
    if boosters or draggers:
        with st.expander("Score drivers", expanded=False):
            for d in boosters:
                st.caption(f"↑ {d['factor']} ({d['value']})")
            for d in draggers:
                st.caption(f"↓ {d['factor']} ({d['value']})")


def _chart_layout(*, show_legend: bool = False, height: int = 260) -> dict:
    return {
        "height": height,
        "margin": dict(t=36, l=8, r=8, b=8),
        "showlegend": show_legend,
    }


def _google_sentiment_counts(reviews: list[dict]) -> dict[str, int]:
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for review in reviews:
        sentiment = review.get("sentiment", "neutral")
        if sentiment not in counts:
            sentiment = "neutral"
        counts[sentiment] += 1
    return counts


def _electricity_payment_split(electricity: dict) -> tuple[int, int]:
    months = len(electricity["monthly_kwh"])
    late = round((1 - electricity["payment_regularity"]) * months)
    return months - late, late


def render_charts(profile: dict, features: dict) -> None:
    gst = profile["gst"]
    upi = profile["upi"]
    aa = profile["aa"]
    epfo = profile["epfo"]
    google = profile["google"]
    courts = profile["courts"]
    electricity = profile["electricity"]
    sector = profile["sector"]

    st.markdown("**Revenue & collections**")
    c1, c2 = st.columns(2)
    with c1:
        df = pd.DataFrame({"Turnover (₹L)": gst["monthly_turnover_lakhs"]})
        fig = px.line(df, markers=True, title="GST turnover")
        fig.update_layout(**_chart_layout())
        st.plotly_chart(fig, width="stretch")
    with c2:
        df = pd.DataFrame({"UPI (₹L)": upi["monthly_volume_lakhs"]})
        fig = px.bar(df, title="UPI collections")
        fig.update_layout(**_chart_layout())
        st.plotly_chart(fig, width="stretch")

    st.markdown("**Operations & payroll**")
    c3, c4 = st.columns(2)
    with c3:
        df = pd.DataFrame({"Credits": aa["monthly_credits_lakhs"], "Debits": aa["monthly_debits_lakhs"]})
        fig = px.area(df, title="Bank cash flow")
        fig.update_layout(**_chart_layout(show_legend=True))
        st.plotly_chart(fig, width="stretch")
    with c4:
        df = pd.DataFrame({"Staff": epfo["employee_count"]})
        fig = px.line(df, markers=True, title="Employee growth")
        fig.update_layout(**_chart_layout())
        st.plotly_chart(fig, width="stretch")

    st.markdown("**Sentiment, sector & risk**")
    c5, c6 = st.columns(2)
    with c5:
        sentiment = _google_sentiment_counts(google.get("reviews", []))
        df = pd.DataFrame(
            {"Sentiment": list(sentiment.keys()), "Reviews": list(sentiment.values())}
        )
        colors = {"positive": "#22C55E", "neutral": "#EAB308", "negative": "#EF4444"}
        fig = px.bar(
            df,
            x="Sentiment",
            y="Reviews",
            title=f"Google business sentiment ({google['rating']}★)",
            color="Sentiment",
            color_discrete_map=colors,
        )
        fig.update_layout(**_chart_layout())
        st.plotly_chart(fig, width="stretch")
    with c6:
        sector_growth = SECTOR_GROWTH.get(sector, features.get("sector_growth_pct", 5.0))
        biz_growth = features["gst_turnover_yoy_growth"]
        df = pd.DataFrame(
            {"Entity": ["Sector", "This business"], "Growth %": [sector_growth, biz_growth]}
        )
        fig = px.bar(df, x="Entity", y="Growth %", title=f"Sector vs business growth ({sector})", color="Entity")
        fig.update_layout(**_chart_layout())
        st.plotly_chart(fig, width="stretch")

    c7, c8 = st.columns(2)
    with c7:
        court_labels = ["Civil", "Criminal", "Insolvency"]
        court_vals = [
            courts["civil_cases"],
            courts["criminal_cases"],
            courts["insolvency_petitions"],
        ]
        df = pd.DataFrame({"Type": court_labels, "Cases": court_vals})
        fig = px.bar(
            df,
            x="Type",
            y="Cases",
            title="Court cases",
            color="Type",
            color_discrete_sequence=["#F97316", "#EF4444", "#991B1B"],
        )
        fig.update_layout(**_chart_layout())
        st.plotly_chart(fig, width="stretch")
    with c8:
        on_time, late = _electricity_payment_split(electricity)
        df = pd.DataFrame({"Status": ["On time", "Late / bounce"], "Months": [on_time, late]})
        fig = px.bar(
            df,
            x="Status",
            y="Months",
            title=f"Electricity bill payments ({electricity['payment_regularity']*100:.0f}% on-time)",
            color="Status",
            color_discrete_map={"On time": "#22C55E", "Late / bounce": "#EF4444"},
        )
        fig.update_layout(**_chart_layout())
        st.plotly_chart(fig, width="stretch")


def render_loan_panel(features: dict, result: dict) -> None:
    score = result["final_score"]
    turnover = features["gst_avg_monthly_turnover"]
    amount = st.slider("Loan amount (₹ Lakhs)", 5, 50, 15)
    out = simulate_loan(score, amount, turnover)

    if out["eligible"]:
        st.success(f"Indicative approval: ₹{out['approved_lakhs']}L at {out.get('interest_rate_pct')}%")
    else:
        st.warning(out["reason"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Max eligible", f"₹{out.get('max_eligible_lakhs', 0)}L")
    c2.metric("Rate", f"{out.get('interest_rate_pct', '—')}%")
    c3.metric("Tenure", f"{out.get('tenure_months', '—')} mo")
