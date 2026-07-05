"""Clean underwriter UI — minimal clutter."""

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.widgets import render_score_gauge
from src.scoring.loan_simulator import simulate_loan
from src.scoring.underwriter_insights import get_credit_decision, get_key_metrics, get_risk_flags
from src.utils.chart_helpers import timeseries_df
from src.utils.constants import SECTOR_GROWTH
from src.utils.ui_text import FINN_SCORE_LABEL
from src.utils.upi_insights import upi_momentum
from src.utils.helpers import avg_recent


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
    cols = st.columns(3)
    for i, m in enumerate(metrics):
        with cols[i % 3]:
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
        with st.expander(f"{FINN_SCORE_LABEL} drivers", expanded=False):
            for d in boosters:
                st.caption(f"↑ {d['factor']} ({d['value']})")
            for d in draggers:
                st.caption(f"↓ {d['factor']} ({d['value']})")


def _chart_layout(*, show_legend: bool = False, height: int = 280) -> dict:
    return {
        "height": height,
        "margin": dict(t=40, l=12, r=12, b=12),
        "showlegend": show_legend,
    }


def _section(title: str) -> None:
    st.markdown(f'<p class="finn-section-title">{title}</p>', unsafe_allow_html=True)


def _plot_chart(fig) -> None:
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch")


def _google_sentiment_counts(reviews: list[dict]) -> dict[str, int]:
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for review in reviews:
        sentiment = review.get("sentiment", "neutral")
        if sentiment not in counts:
            sentiment = "neutral"
        counts[sentiment] += 1
    return counts


def _render_upi_chart(profile: dict) -> None:
    upi = profile["upi"]
    df = timeseries_df(upi["monthly_volume_lakhs"], y_name="Volume (₹L)")
    fig = px.line(
        df,
        x="Month",
        y="Volume (₹L)",
        markers=True,
        title="UPI collection trend",
    )
    fig.update_layout(**_chart_layout())
    _plot_chart(fig)


def _upi_signal_metrics(profile: dict, features: dict) -> list[dict]:
    upi = profile["upi"]
    ticket = upi.get("avg_ticket_size", 0)
    if isinstance(ticket, list):
        avg_ticket = avg_recent(ticket, min(3, len(ticket)))
    else:
        avg_ticket = float(ticket)
    return [
        {"label": "P2M share", "value": f"{upi['p2m_ratio'] * 100:.0f}%"},
        {"label": "6M avg volume", "value": f"₹{features['upi_avg_monthly_volume']:.1f}L"},
        {"label": "Volume YoY", "value": f"{features['upi_volume_yoy_growth']:+.1f}%"},
        {"label": "Failed txn rate", "value": f"{upi['failed_txn_rate'] * 100:.2f}%"},
        {"label": "Avg ticket", "value": f"₹{avg_ticket:,.0f}"},
    ]


def _render_upi_signal(profile: dict, features: dict) -> None:
    upi = profile["upi"]
    metrics = _upi_signal_metrics(profile, features)
    cells = "".join(
        f"<div class='finn-upi-metric'><span class='k'>{m['label']}</span>"
        f"<span class='v'>{m['value']}</span></div>"
        for m in metrics
    )
    st.markdown(
        f"""
        <div class="finn-upi-panel">
            <div>
                <div class="finn-upi-title">UPI merchant signal</div>
                <div class="finn-upi-subtitle">{upi.get('vpa', '—')} · {upi_momentum(upi['monthly_volume_lakhs'])}</div>
            </div>
            <div class="finn-upi-metrics">{cells}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_news_section(profile: dict) -> None:
    st.markdown('<p class="finn-news-heading">News</p>', unsafe_allow_html=True)

    news = profile.get("news", {})
    articles = news.get("articles", [])

    with st.container(border=True):
        if not articles:
            st.caption("No recent headlines available.")
            return
        items = []
        for article in articles[:5]:
            sentiment = article.get("sentiment", "neutral")
            marker = "🟢" if sentiment == "positive" else "🔴" if sentiment == "negative" else "🟡"
            days = article.get("published_days_ago", "—")
            src = article.get("source", "")
            items.append(
                f"<div class='finn-news-item'>{marker} {article['title']}"
                f"<br><span class='finn-muted'>{src} · {days}d ago</span></div>"
            )
        st.markdown(f"<div class='finn-news-list'>{''.join(items)}</div>", unsafe_allow_html=True)


def render_charts(profile: dict, features: dict) -> None:
    gst = profile["gst"]
    aa = profile["aa"]
    epfo = profile["epfo"]
    google = profile["google"]
    electricity = profile["electricity"]
    sector = profile["sector"]

    _section("Revenue & digital collections")
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        df = timeseries_df(gst["monthly_turnover_lakhs"], y_name="Turnover (₹L)")
        fig = px.line(df, x="Month", y="Turnover (₹L)", markers=True, title="GST turnover")
        fig.update_layout(**_chart_layout())
        _plot_chart(fig)
    with c2:
        _render_upi_chart(profile)

    _render_upi_signal(profile, features)

    _section("Operations & payroll")
    c3, c4 = st.columns(2, gap="medium")
    with c3:
        credits = timeseries_df(aa["monthly_credits_lakhs"], y_name="Credits (₹L)")
        debits = timeseries_df(aa["monthly_debits_lakhs"], y_name="Debits (₹L)")
        df = credits.merge(debits, on="Month")
        fig = px.area(df, x="Month", y=["Credits (₹L)", "Debits (₹L)"], title="Bank cash flow")
        fig.update_layout(**_chart_layout(show_legend=True))
        _plot_chart(fig)
    with c4:
        df = timeseries_df([float(x) for x in epfo["employee_count"]], y_name="Staff")
        fig = px.line(df, x="Month", y="Staff", markers=True, title="Employee growth")
        fig.update_layout(**_chart_layout())
        _plot_chart(fig)

    _section("Sentiment & sector")
    c5, c6 = st.columns(2, gap="medium")
    with c5:
        sentiment = _google_sentiment_counts(google.get("reviews", []))
        df = pd.DataFrame({"Sentiment": list(sentiment.keys()), "Reviews": list(sentiment.values())})
        fig = px.bar(
            df,
            x="Sentiment",
            y="Reviews",
            title=f"Google business sentiment ({google['rating']}★)",
            color="Sentiment",
            color_discrete_map={"positive": "#22C55E", "neutral": "#EAB308", "negative": "#EF4444"},
        )
        fig.update_layout(**_chart_layout())
        _plot_chart(fig)
    with c6:
        sector_growth = SECTOR_GROWTH.get(sector, features.get("sector_growth_pct", 5.0))
        biz_growth = features["gst_turnover_yoy_growth"]
        df = pd.DataFrame({"Entity": ["Sector", "This business"], "Growth %": [sector_growth, biz_growth]})
        fig = px.bar(
            df,
            x="Entity",
            y="Growth %",
            title=f"Sector vs business growth ({sector})",
            color="Entity",
        )
        fig.update_layout(**_chart_layout())
        _plot_chart(fig)

    _section("Utilities")
    c7, _ = st.columns([1, 1], gap="medium")
    with c7:
        df = timeseries_df(electricity["monthly_kwh"], y_name="kWh")
        fig = px.line(df, x="Month", y="kWh", markers=True, title="Electricity consumption")
        fig.update_layout(**_chart_layout())
        _plot_chart(fig)

    _render_news_section(profile)


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
