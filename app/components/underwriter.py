"""Collections / RM UI — stress assessment and early-warning signals."""

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.widgets import render_stress_gauge
from src.prediction.stress_insights import get_key_metrics, get_risk_flags, get_stress_decision
from src.prediction.model import load_training_metrics
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
    html = "".join(f"<span class='finn-chip {css}'>{f['label']}</span>" for f in items)
    st.markdown(html, unsafe_allow_html=True)


def render_overview(profile: dict, features: dict, result: dict) -> None:
    stress_pct = int(result["stress_prob"] * 100)
    band = result["band"]
    decision = result.get("decision") or get_stress_decision(result["stress_prob"])

    left, right = st.columns([1.1, 1])
    with left:
        render_stress_gauge(stress_pct, band, result.get("band_color", "#166534"))
    with right:
        color = decision["color"]
        st.markdown(
            f"<p class='finn-decision' style='color:{color};margin-bottom:0.25rem'>{decision['action']}</p>"
            f"<p class='finn-muted'>{decision['headline']}</p>"
            f"<p class='finn-muted'>{result.get('blend_note', '')}</p>",
            unsafe_allow_html=True,
        )

    features["_stress_prob_display"] = result["stress_prob"]
    metrics = get_key_metrics(features, profile)
    cols = st.columns(3)
    for i, m in enumerate(metrics[:6]):
        with cols[i % 3]:
            st.metric(m["label"], m["value"])

    metrics_data = load_training_metrics()
    if metrics_data:
        s_det = metrics_data.get("structured", {}).get("stress_detection_rate", 0) * 100
        f_det = metrics_data.get("full", {}).get("stress_detection_rate", 0) * 100
        with st.expander("Model performance (structured vs full)", expanded=False):
            c1, c2 = st.columns(2)
            s_det = metrics_data.get("structured", {}).get("stress_detection_rate", 0) * 100
            f_det = metrics_data.get("full", {}).get("stress_detection_rate", 0) * 100
            c1.metric("Structured-only stress detection", f"{s_det:.1f}%", help="Legacy static fields — no collections/NLP")
            c2.metric("Full model stress detection", f"{f_det:.1f}%", help="Collections timing + unstructured text features")
            st.caption(
                f"This case: structured ML={result.get('structured_ml_prob', 0)*100:.0f}% · "
                f"full ML={result.get('ml_stress_prob', 0)*100:.0f}% · rule={result.get('rule_stress_prob', 0)*100:.0f}%"
            )

    flags = get_risk_flags(features, profile)
    if flags:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Early warning flags**")
            _chips(flags, ("red", "amber"), "finn-chip-red")
        with c2:
            st.markdown("**Protective signals**")
            _chips(flags, ("green",), "finn-chip-green")

    risks = result.get("risk_factors", [])[:3]
    protective = result.get("protective_factors", [])[:3]
    if risks or protective:
        with st.expander(f"{FINN_SCORE_LABEL} drivers", expanded=False):
            for d in risks:
                st.caption(f"⚠ {d['factor']} ({d['value']})")
            for d in protective:
                st.caption(f"✓ {d['factor']} ({d['value']})")


def _chart_layout(*, show_legend: bool = False, height: int = 280) -> dict:
    return {"height": height, "margin": dict(t=40, l=12, r=12, b=12), "showlegend": show_legend}


def _section(title: str) -> None:
    st.markdown(f'<p class="finn-section-title">{title}</p>', unsafe_allow_html=True)


def _plot_chart(fig) -> None:
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch")


def render_collection_charts(profile: dict, features: dict) -> None:
    panel = profile.get("collections", {}).get("monthly_panel", [])
    if not panel:
        st.caption("No collection panel data.")
        return

    dpd = [m.get("days_past_due", 0) for m in panel]
    paid = [m.get("amount_paid_lakhs", 0) for m in panel]
    due = [m.get("amount_due_lakhs", 0) for m in panel]

    _section("Payment timing & collections")
    c1, c2 = st.columns(2)
    with c1:
        df = timeseries_df(dpd, y_name="Days past due")
        fig = px.bar(df, x="Month", y="Days past due", title="DPD trend (loan under review)")
        fig.update_layout(**_chart_layout())
        _plot_chart(fig)
    with c2:
        df = pd.DataFrame({"Month": [f"M{i+1}" for i in range(len(paid))], "Due": due, "Paid": paid})
        fig = px.line(df, x="Month", y=["Due", "Paid"], markers=True, title="EMI due vs paid")
        fig.update_layout(**_chart_layout(show_legend=True))
        _plot_chart(fig)

    bureau = profile.get("bureau", {})
    other_loans = bureau.get("other_loans", [])
    if other_loans and not bureau.get("is_ntc"):
        _section("Bureau — other loan payment behaviour")
        rows = []
        for loan in other_loans:
            rows.append(
                {
                    "Lender": loan.get("lender"),
                    "Product": loan.get("product"),
                    "On-time %": loan.get("monthly_emi_paid_on_time_rate", 0) * 100,
                    "Avg DPD": loan.get("avg_days_past_due", 0),
                    "Max DPD 12m": max(loan.get("dpd_history_12m", [0])),
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_unstructured_signals(profile: dict, features: dict) -> None:
    unstructured = profile.get("unstructured", {})
    _section("Unstructured → structured conversion")

    conv = [
        ("Review stress score", features.get("review_stress_score", 0)),
        ("News stress score", features.get("news_stress_score", 0)),
        ("RM note stress score", features.get("rm_note_stress_score", 0)),
        ("GST remark stress", features.get("gst_remark_stress_score", 0)),
        ("Collection note stress", features.get("collection_note_stress_score", 0)),
        ("Composite text stress", features.get("composite_text_stress_score", 0)),
    ]
    df = pd.DataFrame({"Signal": [c[0] for c in conv], "Score": [c[1] for c in conv]})
    fig = px.bar(df, x="Score", y="Signal", orientation="h", title="NLP-derived stress features (0–1)")
    fig.update_layout(**_chart_layout())
    _plot_chart(fig)

    with st.expander("Source text evidence", expanded=True):
        for note in unstructured.get("rm_call_notes", [])[:3]:
            st.markdown(f"**RM note** ({note.get('days_ago')}d ago): {note.get('text')}")
        for news in unstructured.get("news_mentions", [])[:3]:
            st.markdown(f"**News** ({news.get('days_ago')}d ago): {news.get('headline')}")
        for gst in unstructured.get("gst_remarks", [])[:2]:
            st.markdown(f"**GST remark** ({gst.get('days_ago')}d ago): {gst.get('text')}")
        for cn in unstructured.get("collection_notes", [])[:2]:
            st.markdown(f"**Collection note** ({cn.get('days_ago')}d ago): {cn.get('text')}")


def render_charts(profile: dict, features: dict) -> None:
    render_collection_charts(profile, features)

    gst = profile["gst"]
    aa = profile["aa"]
    google = profile["google"]
    sector = profile["sector"]

    _section("Revenue & cashflow")
    c1, c2 = st.columns(2)
    with c1:
        df = timeseries_df(gst["monthly_turnover_lakhs"], y_name="Turnover (₹L)")
        fig = px.line(df, x="Month", y="Turnover (₹L)", markers=True, title="GST turnover")
        fig.update_layout(**_chart_layout())
        _plot_chart(fig)
    with c2:
        upi = profile["upi"]
        df = timeseries_df(upi["monthly_volume_lakhs"], y_name="Volume (₹L)")
        fig = px.line(df, x="Month", y="Volume (₹L)", markers=True, title="UPI collections")
        fig.update_layout(**_chart_layout())
        _plot_chart(fig)

    _section("Bank cashflow")
    credits = timeseries_df(aa["monthly_credits_lakhs"], y_name="Credits (₹L)")
    debits = timeseries_df(aa["monthly_debits_lakhs"], y_name="Debits (₹L)")
    df = credits.merge(debits, on="Month")
    fig = px.area(df, x="Month", y=["Credits (₹L)", "Debits (₹L)"], title="Account aggregator cashflow")
    fig.update_layout(**_chart_layout(show_legend=True))
    _plot_chart(fig)

    render_unstructured_signals(profile, features)


def render_loan_panel(profile: dict, features: dict) -> None:
    lb = profile.get("loan_book", {})
    st.markdown("**Active facility**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Loan type", lb.get("loan_type", "—"))
    c2.metric("Sanctioned", f"₹{lb.get('sanctioned_amount_lakhs', 0):.1f}L")
    c3.metric("Outstanding", f"₹{lb.get('outstanding_lakhs', 0):.1f}L")
    c4.metric("EMI / month", f"₹{lb.get('monthly_emi_lakhs', 0):.2f}L")

    bureau = profile.get("bureau", {})
    if bureau.get("is_ntc"):
        st.info("**New-To-Credit (NTC)** — no bureau score. Stress model uses GST, UPI, EPFO, and AA proxies.")
    else:
        st.caption(
            f"Promoter CIBIL: {bureau.get('cibil_score')} · "
            f"Other loans: {len(bureau.get('other_loans', []))} · "
            f"Other-loan on-time: {features.get('bureau_other_emi_on_time_rate', 0)*100:.0f}%"
        )

    render_collection_charts(profile, features)
