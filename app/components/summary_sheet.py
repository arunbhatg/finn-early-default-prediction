"""Summary sheet UI — actual values, drill-down, exportable tables."""

import streamlit as st
import pandas as pd

from src.scoring.summary_data import (
    METRIC_KEYS,
    borrower_identity_table,
    features_table,
    metric_drilldown,
    score_summary_table,
    source_snapshot_tables,
)


def render_metric_row_with_drilldown(features: dict, profile: dict) -> None:
    """Key metrics with popover drill-down on click."""
    from src.scoring.underwriter_insights import get_key_metrics

    st.markdown("#### Key underwriting metrics")
    st.caption("Click **View values** on any metric to see underlying data.")

    metrics = get_key_metrics(features, profile)
    cols = st.columns(len(metrics))

    for col, m in zip(cols, metrics):
        key = METRIC_KEYS.get(m["label"])
        with col:
            st.metric(m["label"], m["value"])
            if key:
                with st.popover("View values"):
                    df = metric_drilldown(key, profile, features)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Bench: {m['benchmark']}")


def render_source_status(status_list: list[dict]) -> None:
    """Show live vs mock badge per connector."""
    live = sum(1 for s in status_list if s["mode"] == "live")
    static = sum(1 for s in status_list if s["mode"] == "static")
    mock = sum(1 for s in status_list if s["mode"] == "mock")
    st.caption(f"**{live} live** · {static} static/reference · {mock} mock (PoC)")

    cols = st.columns(2)
    for i, s in enumerate(status_list):
        badge = {"live": "🟢 LIVE", "static": "🟡 STATIC", "mock": "⚪ MOCK"}.get(s["mode"], "⚪")
        with cols[i % 2]:
            st.markdown(f"**{badge} {s['name']}**")
            st.caption(s["detail"])


def render_summary_sheet(profile: dict, features: dict, result: dict, source_status: list[dict] | None = None) -> None:
    st.markdown("### Data summary sheet")
    st.caption("All actual values pulled for this assessment — suitable for credit memo attachment.")

    tab_id, tab_feat, tab_score, tab_sources, tab_connectors = st.tabs(
        ["Borrower", "All features", "Score breakdown", "By source", "Connector status"]
    )

    with tab_id:
        st.dataframe(borrower_identity_table(profile), use_container_width=True, hide_index=True)
        csv = borrower_identity_table(profile).to_csv(index=False)
        st.download_button("Download borrower CSV", csv, f"{profile['msme_id']}_borrower.csv", "text/csv")

    with tab_feat:
        ft = features_table(features)
        st.dataframe(ft, use_container_width=True, hide_index=True, height=400)
        st.download_button("Download features CSV", ft.to_csv(index=False), f"{profile['msme_id']}_features.csv")

    with tab_score:
        st.dataframe(score_summary_table(result), use_container_width=True, hide_index=True)
        st.markdown("**Score drivers**")
        drivers = []
        for d in result.get("boosters", []):
            drivers.append({"Driver": d["factor"], "Value": d["value"], "Points": f"+{d['score_points']}", "Pillar": d["pillar"]})
        for d in result.get("draggers", []):
            drivers.append({"Driver": d["factor"], "Value": d["value"], "Points": str(d["score_points"]), "Pillar": d["pillar"]})
        if drivers:
            st.dataframe(pd.DataFrame(drivers), use_container_width=True, hide_index=True)

    with tab_sources:
        tables = source_snapshot_tables(profile)
        source = st.selectbox("Select data source", list(tables.keys()))
        df = tables[source]
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            f"Download {source} CSV",
            df.to_csv(index=False),
            f"{profile['msme_id']}_{source.replace(' ', '_')}.csv",
        )

        if source == "Google" and profile["google"].get("reviews"):
            with st.expander("Review text (sample)"):
                for r in profile["google"]["reviews"][:8]:
                    st.markdown(f"**{r['rating']}★** ({r['sentiment']}) — _{r['text']}_")

    with tab_connectors:
        if source_status:
            render_source_status(source_status)
        else:
            st.info("Connector status available after case assessment.")
        st.markdown("[Full integration guide](https://github.com/arunbhatg/finhealth-card/blob/main/docs/CONNECTOR_INTEGRATION.md)")


def render_flags_with_detail(features: dict, profile: dict) -> None:
    from src.scoring.underwriter_insights import get_risk_flags

    flags = get_risk_flags(features, profile)
    if not flags:
        return

    st.markdown("#### Risk & strength flags")
    for f in flags:
        level = f["level"]
        icon = {"red": "🔴", "amber": "🟡", "green": "🟢"}.get(level, "⚪")
        with st.expander(f"{icon} {f['label']} — {f['detail']}"):
            _render_flag_detail(f["label"], profile, features)


def _render_flag_detail(label: str, profile: dict, features: dict) -> None:
    gst, aa, courts, bureau = profile["gst"], profile["aa"], profile["courts"], profile["bureau"]

    if "GST" in label:
        st.dataframe(pd.DataFrame({
            "Month": [f"M-{12-i}" for i in range(12)],
            "Status": gst["filing_status"][-12:],
            "Turnover (₹L)": gst["monthly_turnover_lakhs"][-12:],
        }), hide_index=True)
    elif "EMI" in label or "bounce" in label.lower():
        st.dataframe(pd.DataFrame([
            ("On-time rate", f"{aa['emi_on_time_rate']*100:.1f}%"),
            ("Bounces", aa["bounce_count_12m"]),
            ("OD utilisation", f"{aa['od_utilization']*100:.0f}%"),
        ], columns=["Field", "Value"]), hide_index=True)
    elif "litigation" in label.lower():
        st.dataframe(pd.DataFrame([
            ("Civil", courts["civil_cases"]),
            ("Criminal", courts["criminal_cases"]),
            ("Insolvency", courts["insolvency_petitions"]),
            ("Amount (₹L)", courts["total_outstanding_litigation_lakhs"]),
        ], columns=["Field", "Value"]), hide_index=True)
    elif "CIBIL" in label or "bureau" in label.lower():
        st.dataframe(pd.DataFrame([
            ("Score", bureau["cibil_score"]),
            ("DPD", bureau["dpd_12m"]),
            ("Write-offs", bureau["write_offs_36m"]),
            ("Utilisation", f"{bureau['credit_utilization']*100:.0f}%"),
        ], columns=["Field", "Value"]), hide_index=True)
    elif "growth" in label.lower() or "decline" in label.lower():
        st.dataframe(pd.DataFrame({
            "Month": [f"M-{6-i}" for i in range(6)],
            "GST turnover (₹L)": gst["monthly_turnover_lakhs"][-6:],
        }), hide_index=True)
    elif "ABB" in label:
        st.dataframe(pd.DataFrame({
            "Month": [f"M-{6-i}" for i in range(6)],
            "Balance (₹L)": aa["monthly_closing_balance_lakhs"][-6:],
        }), hide_index=True)
    elif "EPFO" in label or "Payroll" in label:
        epfo = profile["epfo"]
        st.dataframe(pd.DataFrame({
            "Month": [f"M-{6-i}" for i in range(6)],
            "Employees": epfo["employee_count"][-6:],
            "Status": epfo["contribution_status"][-6:],
        }), hide_index=True)
    elif "sentiment" in label.lower() or "Google" in label:
        g = profile["google"]
        st.write(f"Rating: {g['rating']} | Reviews: {g['review_count']}")
        for r in g["reviews"][:5]:
            st.caption(f"{r['rating']}★ {r['sentiment']}: {r['text']}")
    else:
        st.json({k: v for k, v in features.items() if k in ("gst_filing_compliance", "gst_turnover_yoy_growth")})
