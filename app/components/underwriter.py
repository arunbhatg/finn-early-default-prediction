"""Collections / RM UI — underwriter-first layout."""

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.widgets import render_stress_gauge
from src.prediction import stress_insights as _stress_insights
from src.prediction.stress_insights import get_risk_flags, get_stress_decision
from src.utils.chart_helpers import timeseries_df
from src.utils.display_helpers import (
    build_text_signal_table,
    collect_text_timeline,
    describe_month_on_book,
    get_derived_business_metrics,
    get_text_intel_metrics,
    text_severity_label,
)
from src.utils.ui_text import FINN_SCORE_LABEL, STRESS_RISK_EXPLAINER, TAB_BUSINESS_SIGNALS


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
    cols = st.columns(columns)
    for i, m in enumerate(metrics):
        with cols[i % columns]:
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


def render_overview(profile: dict, features: dict, result: dict) -> None:
    """Underwriter decision view — action, payment signals, derived intel, flags, drivers."""
    stress_pct = int(result["stress_prob"] * 100)
    band = result["band"]
    decision = result.get("decision") or get_stress_decision(result["stress_prob"])
    case_key = profile.get("msme_id", "case")
    features["_stress_prob_display"] = result["stress_prob"]
    obs_info = describe_month_on_book(profile, result.get("observation_month"))

    render_decision_banner(result, month_on_book=obs_info["short"])
    st.caption(STRESS_RISK_EXPLAINER)

    gauge_col, detail_col = st.columns([1, 1.35], gap="large")
    with gauge_col:
        with st.container(border=True):
            render_stress_gauge(stress_pct, band, result.get("band_color", "#166534"), chart_key=f"gauge_{case_key}")
    with detail_col:
        with st.container(border=True):
            st.markdown(f"**{decision['action']}** — {decision['headline']}")
            if result.get("blend_note"):
                st.caption(result["blend_note"])
            lb = profile.get("loan_book", {})
            m1, m2, m3 = st.columns(3, gap="small")
            m1.metric("Month on book", str(obs_info["month"]))
            m2.metric("Outstanding", f"₹{lb.get('outstanding_lakhs', 0):.1f}L")
            m3.metric("EMI / month", f"₹{lb.get('monthly_emi_lakhs', 0):.2f}L")
            st.caption(f"{lb.get('loan_type', '—')} · {profile.get('city', '—')}")
            with st.expander("About month on book", expanded=False):
                st.markdown(str(obs_info["long"]))

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

    risks = result.get("risk_factors", [])[:4]
    protective = result.get("protective_factors", [])[:3]
    expand_drivers = result["stress_prob"] >= 0.45
    with st.expander(f"{FINN_SCORE_LABEL} drivers", expanded=expand_drivers):
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


def render_text_intel_compact(profile: dict, features: dict, *, key_prefix: str = "nlp") -> None:
    rows = build_text_signal_table(profile, features)
    if not rows and features.get("composite_text_stress_score", 0) <= 0:
        return

    _section("Text & market signals")
    _metric_row(get_text_intel_metrics(features), columns=4)

    if rows:
        c1, c2 = st.columns([1.2, 1], gap="medium")
        with c1:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        with c2:
            _text_stress_chart(features, key=f"{key_prefix}_bar", height=260)

        composite = features.get("composite_text_stress_score", 0)
        st.caption(
            f"Composite text stress index: **{composite * 100:.0f}/100** ({text_severity_label(composite)}) — "
            "derived from keyword and sentiment analysis on reviews, news, RM notes, GST remarks, and collection notes."
        )


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
        st.caption("New-to-Credit — CIBIL not available; GST, UPI, and bank data used in scoring.")
    else:
        st.caption(
            f"Promoter CIBIL **{bureau.get('cibil_score')}** · "
            f"{len(bureau.get('other_loans', []))} other bureau loan(s) · "
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
        fig.update_layout(**_chart_layout(height=260), showlegend=True)
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
    _section("Unstructured text → structured features")
    render_text_intel_compact(profile, features, key_prefix=key_prefix)

    rows = build_text_signal_table(profile, features)
    if rows:
        st.markdown("**Structured conversion by source**")
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

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

    composite = features.get("composite_text_stress_score", 0)
    with st.expander("How text scores are computed", expanded=False):
        st.markdown(
            "Each text source is scanned for stress keywords (e.g. *overdue, bounce, restructuring, default*) "
            "and positive signals (*timely, growth*). Keyword density is converted to a **0–100 structured score** "
            "per source, then blended into the composite text stress index used by the model."
        )
        st.caption(f"Composite index for this case: **{composite * 100:.0f}/100** ({text_severity_label(composite)})")


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
    return TAB_BUSINESS_SIGNALS
