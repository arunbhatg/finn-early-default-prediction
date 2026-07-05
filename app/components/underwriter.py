"""Collections / RM UI — underwriter-first layout."""

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.widgets import render_stress_gauge
from src.prediction import stress_insights as _stress_insights
from src.prediction.model import load_training_metrics
from src.prediction.stress_insights import get_risk_flags, get_stress_decision
from src.utils.chart_helpers import timeseries_df
from src.utils.ui_text import FINN_SCORE_LABEL


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


def render_decision_banner(result: dict) -> None:
    decision = result.get("decision") or get_stress_decision(result["stress_prob"])
    stress_pct = int(result["stress_prob"] * 100)
    st.markdown(
        f"""
        <div class="finn-decision-banner" style="border-left-color:{decision['color']}">
            <div class="finn-decision-banner-action" style="color:{decision['color']}">{decision['action']}</div>
            <div class="finn-decision-banner-meta">
                <span><strong>{stress_pct}%</strong> stress (12m)</span>
                <span class="finn-decision-banner-sep">·</span>
                <span>{decision['band']} band</span>
                <span class="finn-decision-banner-sep">·</span>
                <span>{decision['headline']}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview(profile: dict, features: dict, result: dict) -> None:
    """Underwriter decision view — action, payment signals, flags, drivers."""
    stress_pct = int(result["stress_prob"] * 100)
    band = result["band"]
    decision = result.get("decision") or get_stress_decision(result["stress_prob"])
    case_key = profile.get("msme_id", "case")
    features["_stress_prob_display"] = result["stress_prob"]

    render_decision_banner(result)

    gauge_col, detail_col = st.columns([1, 1.35], gap="large")
    with gauge_col:
        with st.container(border=True):
            render_stress_gauge(stress_pct, band, result.get("band_color", "#166534"), chart_key=f"gauge_{case_key}")
    with detail_col:
        with st.container(border=True):
            st.markdown(f"**Recommended action:** `{decision['action']}`")
            st.caption(decision["headline"])
            st.caption(result.get("blend_note", ""))
            obs = result.get("observation_month", "—")
            lb = profile.get("loan_book", {})
            st.markdown(
                f"- **Loan:** {lb.get('loan_type', '—')} · ₹{lb.get('outstanding_lakhs', 0):.1f}L outstanding  \n"
                f"- **Horizon:** 12 months · observation month **{obs}**  \n"
                f"- **Credit path:** {'NTC (alt-data)' if profile.get('bureau', {}).get('is_ntc') else 'Bureau file'}"
            )

    st.markdown('<p class="finn-section-title">① Payment & collections (priority)</p>', unsafe_allow_html=True)
    _metric_row(_payment_metrics(features, profile), columns=4)

    st.markdown('<p class="finn-section-title">② Facility snapshot</p>', unsafe_allow_html=True)
    _metric_row(_facility_metrics(features, profile), columns=4)

    flags = get_risk_flags(features, profile)
    if flags:
        st.markdown('<p class="finn-section-title">③ Early warning flags</p>', unsafe_allow_html=True)
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
    with st.expander(f"④ {FINN_SCORE_LABEL} drivers", expanded=expand_drivers):
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

    metrics_data = load_training_metrics()
    if metrics_data:
        with st.expander("Model uplift (structured-only vs full)", expanded=False):
            s_det = metrics_data.get("structured", {}).get("stress_detection_rate", 0) * 100
            f_det = metrics_data.get("full", {}).get("stress_detection_rate", 0) * 100
            c1, c2 = st.columns(2)
            c1.metric("Legacy structured-only", f"{s_det:.1f}%", help="No collections timing / NLP")
            c2.metric("Full FINN. model", f"{f_det:.1f}%", help="Collections + bureau other-loans + text")
            st.caption(
                f"This case — structured ML: {result.get('structured_ml_prob', 0)*100:.0f}% · "
                f"full ML: {result.get('ml_stress_prob', 0)*100:.0f}% · "
                f"rules: {result.get('rule_stress_prob', 0)*100:.0f}%"
            )


def _chart_layout(*, show_legend: bool = False, height: int = 300) -> dict:
    return {"height": height, "margin": dict(t=36, l=8, r=8, b=8), "showlegend": show_legend}


def _section(title: str) -> None:
    st.markdown(f'<p class="finn-section-title">{title}</p>', unsafe_allow_html=True)


def _plot_chart(fig, key: str) -> None:
    st.plotly_chart(fig, width="stretch", key=key)


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
        st.info("**New-To-Credit (NTC)** — stress model uses GST, UPI, EPFO, and AA proxies instead of bureau score.")
    else:
        st.caption(
            f"Promoter CIBIL **{bureau.get('cibil_score')}** · "
            f"{len(bureau.get('other_loans', []))} other bureau loan(s) · "
            f"other-loan on-time **{features.get('bureau_other_emi_on_time_rate', 0)*100:.0f}%**"
        )


def render_alt_data_charts(profile: dict, features: dict, *, key_prefix: str = "alt") -> None:
    gst = profile["gst"]
    aa = profile["aa"]

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


def render_unstructured_signals(profile: dict, features: dict, *, key_prefix: str = "nlp") -> None:
    unstructured = profile.get("unstructured", {})

    conv = [
        ("Review stress", features.get("review_stress_score", 0)),
        ("News stress", features.get("news_stress_score", 0)),
        ("RM note stress", features.get("rm_note_stress_score", 0)),
        ("GST remark stress", features.get("gst_remark_stress_score", 0)),
        ("Collection note stress", features.get("collection_note_stress_score", 0)),
        ("Composite text stress", features.get("composite_text_stress_score", 0)),
    ]
    df = pd.DataFrame({"Signal": [c[0] for c in conv], "Score": [c[1] for c in conv]})
    fig = px.bar(df, x="Score", y="Signal", orientation="h", title="Unstructured → structured stress scores")
    fig.update_layout(**_chart_layout())
    _plot_chart(fig, key=f"{key_prefix}_stress_bar")

    with st.expander("Source text evidence", expanded=result_expanded(features)):
        for note in unstructured.get("rm_call_notes", [])[:3]:
            st.markdown(f"**RM note** ({note.get('days_ago')}d ago): {note.get('text')}")
        for news in unstructured.get("news_mentions", [])[:3]:
            st.markdown(f"**News** ({news.get('days_ago')}d ago): {news.get('headline')}")
        for gst in unstructured.get("gst_remarks", [])[:2]:
            st.markdown(f"**GST remark** ({gst.get('days_ago')}d ago): {gst.get('text')}")
        for cn in unstructured.get("collection_notes", [])[:2]:
            st.markdown(f"**Collection note** ({cn.get('days_ago')}d ago): {cn.get('text')}")
        if not any(
            unstructured.get(k)
            for k in ("rm_call_notes", "news_mentions", "gst_remarks", "collection_notes")
        ):
            st.caption("No unstructured text on file.")


def result_expanded(features: dict) -> bool:
    return features.get("composite_text_stress_score", 0) >= 0.25
