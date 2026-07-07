"""Collections / RM UI — underwriter-first layout."""

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.widgets import render_stress_gauge
from src.prediction import stress_insights as _stress_insights
from src.prediction.stress_insights import get_risk_flags, get_stress_decision
from src.utils.chart_helpers import timeseries_df
from src.utils import display_helpers as _display_helpers
from src.utils.display_helpers import (
    build_text_signal_table,
    collect_text_timeline,
    describe_month_on_book,
    get_derived_business_metrics,
    get_text_intel_metrics,
    text_severity_label,
)
from src.utils import ui_text as _ui_text

_NEWS_SENTIMENT_SCORE = {"positive": 1, "neutral": 0, "negative": -1}
_NEWS_SENTIMENT_LABEL = {"positive": "Positive", "neutral": "Neutral", "negative": "Negative"}


def _fallback_collect_recent_news(profile: dict, *, limit: int = 6, max_days: int = 365) -> list[dict]:
    items = profile.get("unstructured", {}).get("news_mentions", [])
    news = []
    for item in items:
        days = int(item.get("days_ago", 999))
        if days > max_days:
            continue
        sentiment = item.get("sentiment", "neutral")
        event_date = date.today() - timedelta(days=days)
        news.append(
            {
                "days_ago": days,
                "date_label": event_date.strftime("%d %b %Y"),
                "sentiment": sentiment,
                "sentiment_label": _NEWS_SENTIMENT_LABEL.get(sentiment, "Neutral"),
                "headline": item.get("headline", "").strip(),
                "text": item.get("text", "").strip(),
            }
        )
    news.sort(key=lambda n: n["days_ago"])
    return news[:limit]


def _fallback_build_news_sentiment_dataframe(profile: dict, *, max_days: int = 365) -> pd.DataFrame:
    rows = []
    for item in _fallback_collect_recent_news(profile, limit=50, max_days=max_days):
        rows.append(
            {
                "Date": date.today() - timedelta(days=int(item["days_ago"])),
                "Days ago": item["days_ago"],
                "Sentiment score": _NEWS_SENTIMENT_SCORE.get(item["sentiment"], 0),
                "Sentiment": item["sentiment_label"],
                "Headline": item["headline"],
                "Summary": item["text"],
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("Date")


def _collect_recent_news(profile: dict, *, limit: int = 6, max_days: int = 365) -> list[dict]:
    fn = getattr(_display_helpers, "collect_recent_news", None)
    if fn is not None:
        return fn(profile, limit=limit, max_days=max_days)
    return _fallback_collect_recent_news(profile, limit=limit, max_days=max_days)


def _build_news_sentiment_dataframe(profile: dict, *, max_days: int = 365) -> pd.DataFrame:
    fn = getattr(_display_helpers, "build_news_sentiment_dataframe", None)
    if fn is not None:
        return fn(profile, max_days=max_days)
    return _fallback_build_news_sentiment_dataframe(profile, max_days=max_days)


def _insights_section_title() -> str:
    return getattr(_ui_text, "SECTION_UNSTRUCTURED_INSIGHTS", "Insights from unstructured signals")


def _payment_metrics(features: dict, profile: dict) -> list[dict]:
    fn = getattr(_stress_insights, "get_payment_metrics", None)
    if fn is not None:
        return fn(features, profile)
    metrics = _stress_insights.get_key_metrics(features, profile)
    return metrics[:4]


def _facility_metrics(features: dict, profile: dict) -> list[dict]:
    fn = getattr(_stress_insights, "get_facility_metrics", None)
    if fn is not None:
        return fn(features, profile)
    metrics = _stress_insights.get_key_metrics(features, profile)
    return metrics[4:8] if len(metrics) > 4 else metrics[4:]


def _chips(flags: list[dict], levels: tuple[str, ...], css: str, limit: int = 4) -> None:
    items = [f for f in flags if f["level"] in levels][:limit]
    if not items:
        st.caption("—")
        return
    html = "".join(f"<span class='finn-chip {css}'>{f['label']}</span>" for f in items)
    st.markdown(html, unsafe_allow_html=True)


def _metric_row(metrics: list[dict], columns: int = 4) -> None:
    cols = st.columns(columns, gap="small")
    for i, m in enumerate(metrics[:columns]):
        with cols[i]:
            st.metric(m["label"], m["value"])


def render_decision_banner(result: dict, *, month_on_book: str = "") -> None:
    decision = result.get("decision") or get_stress_decision(result["stress_prob"])
    stress_pct = int(result["stress_prob"] * 100)
    mob = f'<span class="finn-decision-banner-sep">·</span><span>{month_on_book}</span>' if month_on_book else ""
    st.markdown(
        f"""
        <div class="finn-decision-banner" style="border-left-color:{decision['color']}">
            <div class="finn-decision-banner-action" style="color:{decision['color']}">{decision['action']}</div>
            <div class="finn-decision-banner-meta">
                <span><strong>{stress_pct}%</strong> 12-month stress risk</span>
                <span class="finn-decision-banner-sep">·</span>
                <span>{decision['band']} band</span>
                {mob}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_hero(
    *,
    stress_pct: int,
    band: str,
    band_color: str,
    decision: dict,
    profile: dict,
    lb: dict,
    obs_info: dict,
    chart_key: str,
) -> None:
    """Single-card hero: gauge left, action context right — aligned in one row."""
    st.markdown('<div class="finn-hero-anchor"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        gauge_col, action_col = st.columns([2, 3], gap="small")
        with gauge_col:
            render_stress_gauge(stress_pct, band, band_color, chart_key=chart_key, compact=True)
        with action_col:
            st.markdown(
                f"""
                <div class="finn-action-stack">
                    <p class="finn-action-headline">
                        <span style="color:{decision['color']}">{decision['action']}</span>
                        — {decision['headline']}
                    </p>
                    <div class="finn-action-facts">
                        <div class="finn-action-fact">
                            <span class="k">Month on book</span>
                            <span class="v">{obs_info['month']}</span>
                        </div>
                        <div class="finn-action-fact">
                            <span class="k">Outstanding</span>
                            <span class="v">₹{lb.get('outstanding_lakhs', 0):.1f}L</span>
                        </div>
                        <div class="finn-action-fact">
                            <span class="k">EMI / month</span>
                            <span class="v">₹{lb.get('monthly_emi_lakhs', 0):.2f}L</span>
                        </div>
                        <div class="finn-action-fact">
                            <span class="k">Risk band</span>
                            <span class="v" style="color:{decision['color']}">{band}</span>
                        </div>
                    </div>
                    <p class="finn-action-meta">
                        <strong>{lb.get('loan_type', '—')}</strong> · {profile.get('city', '—')} · {obs_info['short']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_overview(profile: dict, features: dict, result: dict) -> None:
    """Underwriter decision view — action, drivers, payment signals, intel, flags."""
    stress_pct = int(result["stress_prob"] * 100)
    band = result["band"]
    decision = result.get("decision") or get_stress_decision(result["stress_prob"])
    case_key = profile.get("msme_id", "case")
    features["_stress_prob_display"] = result["stress_prob"]
    obs_info = describe_month_on_book(profile, result.get("observation_month"))

    render_decision_banner(result, month_on_book=obs_info["short"])

    lb = profile.get("loan_book", {})
    render_decision_hero(
        stress_pct=stress_pct,
        band=band,
        band_color=result.get("band_color", "#166534"),
        decision=decision,
        profile=profile,
        lb=lb,
        obs_info=obs_info,
        chart_key=f"gauge_{case_key}",
    )

    risks = result.get("risk_factors", [])[:4]
    protective = result.get("protective_factors", [])[:3]
    expand_drivers = result["stress_prob"] >= 0.45
    with st.expander(f"{_ui_text.FINN_SCORE_LABEL} drivers", expanded=expand_drivers):
        d1, d2 = st.columns(2, gap="medium")
        with d1:
            st.markdown("**Risk factors**")
            if risks:
                for d in risks:
                    st.markdown(f"- {d['factor']} — *{d['value']}*")
            else:
                st.caption("None flagged")
        with d2:
            st.markdown("**Protective factors**")
            if protective:
                for d in protective:
                    st.markdown(f"- {d['factor']} — *{d['value']}*")
            else:
                st.caption("None flagged")

    st.markdown('<p class="finn-section-title">Payment & collections</p>', unsafe_allow_html=True)
    _metric_row(_payment_metrics(features, profile), columns=4)

    st.markdown('<p class="finn-section-title">Facility</p>', unsafe_allow_html=True)
    _metric_row(_facility_metrics(features, profile), columns=4)

    st.markdown('<p class="finn-section-title">Business signals</p>', unsafe_allow_html=True)
    _metric_row(get_derived_business_metrics(features, profile), columns=4)

    render_text_intel_compact(profile, features, key_prefix=f"decision_nlp_{case_key}")

    flags = get_risk_flags(features, profile)
    if flags:
        st.markdown('<p class="finn-section-title">Early warning flags</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            st.markdown("**Concerns**")
            _chips(flags, ("red", "amber"), "finn-chip-red")
        with c2:
            st.markdown("**Strengths**")
            _chips(flags, ("green",), "finn-chip-green")


def _chart_layout(*, show_legend: bool = False, height: int = 300) -> dict:
    return {"height": height, "margin": dict(t=36, l=8, r=8, b=8), "showlegend": show_legend}


def _section(title: str) -> None:
    st.markdown(f'<p class="finn-section-title">{title}</p>', unsafe_allow_html=True)


def _plot_chart(fig, key: str) -> None:
    st.plotly_chart(fig, width="stretch", key=key)


def _text_stress_chart(features: dict, *, key: str, height: int = 280) -> None:
    conv = [
        ("Reviews", features.get("review_stress_score", 0)),
        ("News", features.get("news_stress_score", 0)),
        ("RM notes", features.get("rm_note_stress_score", 0)),
        ("GST remarks", features.get("gst_remark_stress_score", 0)),
        ("Collection notes", features.get("collection_note_stress_score", 0)),
    ]
    df = pd.DataFrame({"Source": [c[0] for c in conv], "Score": [c[1] * 100 for c in conv]})
    fig = px.bar(
        df,
        x="Score",
        y="Source",
        orientation="h",
        title="Text → structured stress scores (0–100)",
        color="Score",
        color_continuous_scale=["#DCFCE7", "#FEF9C3", "#FEE2E2"],
        range_color=[0, 100],
    )
    fig.update_layout(**_chart_layout(height=height), coloraxis_showscale=False)
    _plot_chart(fig, key=key)


def _news_sentiment_chart(profile: dict, *, key: str) -> None:
    df = _build_news_sentiment_dataframe(profile)
    if df.empty:
        return
    fig = px.scatter(
        df,
        x="Date",
        y="Sentiment score",
        color="Sentiment",
        color_discrete_map={"Negative": "#EF4444", "Neutral": "#94A3B8", "Positive": "#22C55E"},
        hover_name="Headline",
        custom_data=["Summary", "Days ago"],
        title="News sentiment timeline",
        labels={"Sentiment score": "Sentiment", "Date": "Publication date"},
    )
    fig.update_traces(marker={"size": 11, "line": {"width": 1, "color": "white"}})
    layout = _chart_layout(height=280, show_legend=True)
    layout["yaxis"] = dict(
        tickmode="array",
        tickvals=[-1, 0, 1],
        ticktext=["Negative", "Neutral", "Positive"],
        range=[-1.35, 1.35],
    )
    fig.update_layout(**layout)
    _plot_chart(fig, key=key)


def _render_recent_news_text(profile: dict) -> None:
    news_items = _collect_recent_news(profile)
    if not news_items:
        st.caption("No recent news mentions on file.")
        return

    st.markdown("**Recent news headlines**")
    for item in news_items:
        sentiment = item.get("sentiment", "neutral")
        css = {"negative": "finn-event-negative", "positive": "finn-event-positive"}.get(
            sentiment, "finn-event-neutral"
        )
        body = item["text"] or item["headline"]
        st.markdown(
            f'<div class="finn-event {css}">'
            f'<span class="finn-event-meta">{item["date_label"]} · {item["sentiment_label"]}</span>'
            f"<strong>{item['headline']}</strong><br>{body}"
            f"</div>",
            unsafe_allow_html=True,
        )


def render_text_intel_compact(profile: dict, features: dict, *, key_prefix: str = "nlp", show_section: bool = True) -> None:
    rows = build_text_signal_table(profile, features)
    has_news = bool(_collect_recent_news(profile))
    if not rows and features.get("composite_text_stress_score", 0) <= 0 and not has_news:
        return

    if show_section:
        _section(_insights_section_title())

    if rows or features.get("composite_text_stress_score", 0) > 0:
        _metric_row(get_text_intel_metrics(features), columns=4)

    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        _text_stress_chart(features, key=f"{key_prefix}_bar", height=240)

        composite = features.get("composite_text_stress_score", 0)
        st.caption(
            f"Composite text stress index: **{composite * 100:.0f}/100** ({text_severity_label(composite)}) — "
            "derived from keyword and sentiment analysis on reviews, news, RM notes, GST remarks, and collection notes."
        )

    if has_news:
        st.markdown("**News & media**")
        c1, c2 = st.columns([1.1, 1], gap="medium")
        with c1:
            _render_recent_news_text(profile)
        with c2:
            _news_sentiment_chart(profile, key=f"{key_prefix}_news_sentiment")


def render_collection_charts(profile: dict, features: dict, *, key_prefix: str = "coll") -> None:
    panel = profile.get("collections", {}).get("monthly_panel", [])
    if not panel:
        st.caption("No collection panel data.")
        return

    dpd = [m.get("days_past_due", 0) for m in panel]
    paid = [m.get("amount_paid_lakhs", 0) for m in panel]
    due = [m.get("amount_due_lakhs", 0) for m in panel]

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        df = timeseries_df(dpd, y_name="Days past due")
        fig = px.bar(df, x="Month", y="Days past due", title="DPD trend")
        fig.update_layout(**_chart_layout())
        _plot_chart(fig, key=f"{key_prefix}_dpd")
    with c2:
        df = pd.DataFrame({"Month": [f"M{i+1}" for i in range(len(paid))], "Due": due, "Paid": paid})
        fig = px.line(df, x="Month", y=["Due", "Paid"], markers=True, title="EMI due vs paid")
        fig.update_layout(**_chart_layout(show_legend=True))
        _plot_chart(fig, key=f"{key_prefix}_emi")

    bureau = profile.get("bureau", {})
    other_loans = bureau.get("other_loans", [])
    if other_loans and not bureau.get("is_ntc"):
        _section("Bureau — other loan payment behaviour")
        rows = [
            {
                "Lender": loan.get("lender"),
                "Product": loan.get("product"),
                "On-time %": round(loan.get("monthly_emi_paid_on_time_rate", 0) * 100, 1),
                "Avg DPD": loan.get("avg_days_past_due", 0),
                "Max DPD 12m": max(loan.get("dpd_history_12m", [0])),
            }
            for loan in other_loans
        ]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    commercial = bureau.get("commercial", {})
    if commercial.get("has_file") and not bureau.get("is_ntc"):
        _section("Commercial bureau — entity facilities")
        st.caption(
            f"**{commercial.get('entity_name', '—')}** · CMR rank **{commercial.get('cmr_rank')}** "
            f"(1 = lowest risk) · max DPD **{commercial.get('max_dpd_12m', 0)}d** · "
            f"utilization **{commercial.get('utilization', 0)*100:.0f}%**"
        )
        facilities = commercial.get("facilities", [])
        if facilities:
            comm_rows = [
                {
                    "Lender": f.get("lender"),
                    "Product": f.get("product"),
                    "Outstanding (₹L)": f.get("outstanding_lakhs"),
                    "On-time %": round(f.get("monthly_emi_paid_on_time_rate", 0) * 100, 1),
                    "Max DPD 12m": f.get("max_dpd_12m", 0),
                }
                for f in facilities
            ]
            st.dataframe(pd.DataFrame(comm_rows), width="stretch", hide_index=True)


def render_loan_panel(profile: dict, features: dict) -> None:
    lb = profile.get("loan_book", {})
    bureau = profile.get("bureau", {})

    _metric_row(
        [
            {"label": "Loan type", "value": lb.get("loan_type", "—")},
            {"label": "Sanctioned", "value": f"₹{lb.get('sanctioned_amount_lakhs', 0):.1f}L"},
            {"label": "Outstanding", "value": f"₹{lb.get('outstanding_lakhs', 0):.1f}L"},
            {"label": "EMI / month", "value": f"₹{lb.get('monthly_emi_lakhs', 0):.2f}L"},
        ],
        columns=4,
    )

    if bureau.get("is_ntc"):
        st.caption("New-to-Credit — promoter/commercial bureau not available; GST, UPI, and bank data used.")
    else:
        commercial = bureau.get("commercial", {})
        comm_line = (
            f"Commercial CMR **{commercial.get('cmr_rank')}** · "
            f"{commercial.get('facility_count', 0)} entity facility(ies)"
            if commercial.get("has_file")
            else "Commercial bureau **not on file**"
        )
        st.caption(
            f"Promoter CIBIL **{bureau.get('cibil_score')}** · {comm_line} · "
            f"{len(bureau.get('other_loans', []))} other consumer tradeline(s) · "
            f"other-loan on-time **{features.get('bureau_other_emi_on_time_rate', 0)*100:.0f}%**"
        )


def render_alt_data_charts(profile: dict, features: dict, *, key_prefix: str = "alt") -> None:
    gst = profile["gst"]
    aa = profile["aa"]

    filing = gst.get("filing_status", [])
    if filing:
        obs = min(len(filing), 12)
        recent = filing[-obs:]
        status_df = pd.DataFrame(
            {
                "Month": [f"M{i+1}" for i in range(len(recent))],
                "Status": recent,
                "Score": [1 if s == "filed" else 0.5 if s == "delayed" else 0 for s in recent],
            }
        )
        fig = px.bar(
            status_df,
            x="Month",
            y="Score",
            color="Status",
            title="GST filing status (recent months)",
            color_discrete_map={"filed": "#22C55E", "delayed": "#F59E0B", "missed": "#EF4444"},
        )
        fig.update_layout(**_chart_layout(height=260, show_legend=True))
        _plot_chart(fig, key=f"{key_prefix}_gst_filing")

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        df = timeseries_df(gst["monthly_turnover_lakhs"], y_name="Turnover (₹L)")
        fig = px.line(df, x="Month", y="Turnover (₹L)", markers=True, title="GST turnover")
        fig.update_layout(**_chart_layout())
        _plot_chart(fig, key=f"{key_prefix}_gst")
    with c2:
        upi = profile["upi"]
        df = timeseries_df(upi["monthly_volume_lakhs"], y_name="Volume (₹L)")
        fig = px.line(df, x="Month", y="Volume (₹L)", markers=True, title="UPI collections")
        fig.update_layout(**_chart_layout())
        _plot_chart(fig, key=f"{key_prefix}_upi")

    credits = timeseries_df(aa["monthly_credits_lakhs"], y_name="Credits (₹L)")
    debits = timeseries_df(aa["monthly_debits_lakhs"], y_name="Debits (₹L)")
    df = credits.merge(debits, on="Month")
    fig = px.area(df, x="Month", y=["Credits (₹L)", "Debits (₹L)"], title="Bank cashflow (AA)")
    fig.update_layout(**_chart_layout(show_legend=True))
    _plot_chart(fig, key=f"{key_prefix}_cashflow")

    _metric_row(get_derived_business_metrics(features, profile), columns=4)


def render_unstructured_signals(profile: dict, features: dict, *, key_prefix: str = "nlp") -> None:
    render_text_intel_compact(profile, features, key_prefix=key_prefix, show_section=True)

    timeline = collect_text_timeline(profile)
    if timeline:
        st.markdown("**Recent text events**")
        for event in timeline:
            sentiment = event.get("sentiment", "neutral")
            css = {"negative": "finn-event-negative", "positive": "finn-event-positive"}.get(sentiment, "finn-event-neutral")
            st.markdown(
                f'<div class="finn-event {css}">'
                f'<span class="finn-event-meta">{event["source"]} · {event["days_ago"]}d ago</span>'
                f'{event["text"][:180]}{"…" if len(event["text"]) > 180 else ""}'
                f"</div>",
                unsafe_allow_html=True,
            )


def render_evidence_summary(profile: dict, features: dict, result: dict) -> None:
    obs = describe_month_on_book(profile, result.get("observation_month"))
    decision = result.get("decision") or get_stress_decision(result["stress_prob"])
    st.markdown(
        f"**{obs['short']}** · **{int(result['stress_prob'] * 100)}%** stress risk · "
        f"**{decision['action']}** ({result['band']})"
    )
    summary = (
        _payment_metrics(features, profile)[:2]
        + get_derived_business_metrics(features, profile)[:2]
        + get_text_intel_metrics(features)[:2]
    )
    _metric_row(summary[:6], columns=3)


def tab_business_signals_label() -> str:
    return getattr(_ui_text, "TAB_BUSINESS_SIGNALS", "Business & Digital Signals")
