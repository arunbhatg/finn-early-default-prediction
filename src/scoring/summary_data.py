"""Build tabular summary data for underwriter drill-down."""

from __future__ import annotations

import pandas as pd

from src.utils.constants import MACRO_INDICATORS, SECTOR_GROWTH
from src.utils.display_metrics import active_litigation_label
from src.utils.helpers import avg_recent, compliance_rate, yoy_growth
from src.utils.ui_text import FINN_SCORE_LABEL


def _kv_table(rows: list[tuple], columns: tuple[str, str] = ("Field", "Value")) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=list(columns))
    df[columns[1]] = df[columns[1]].astype(str)
    return df


def borrower_identity_table(profile: dict) -> pd.DataFrame:
    rows = [
        ("Business name", profile["business_name"]),
        ("MSME ID", profile["msme_id"]),
        ("GSTIN", profile["gstin"]),
        ("PAN", profile["pan"]),
        ("Udyam", profile.get("udyam_number", "—")),
        ("Sector", profile["sector"]),
        ("Location", f"{profile['city']}, {profile['state']}"),
        ("Years in business", str(profile["years_in_business"])),
        ("Promoter", profile["bureau"]["promoter_name"]),
    ]
    return _kv_table(rows)


def features_table(features: dict) -> pd.DataFrame:
    rows = []
    for key, val in sorted(features.items()):
        if key in ("msme_id", "sector"):
            continue
        if isinstance(val, float):
            display = f"{val:.2f}" if abs(val) < 1000 else f"{val:,.2f}"
        else:
            display = str(val)
        rows.append({"Feature": key, "Value": display})
    return pd.DataFrame(rows)


def metric_drilldown(metric_key: str, profile: dict, features: dict) -> pd.DataFrame:
    """Return actual underlying values for a key metric."""
    gst = profile["gst"]
    aa = profile["aa"]
    epfo = profile["epfo"]
    bureau = profile["bureau"]

    if metric_key == "gst_compliance":
        statuses = gst["filing_status"][-12:]
        return pd.DataFrame({
            "Month": [f"M-{12-i}" for i in range(12)],
            "Filing status": statuses,
        })
    if metric_key == "turnover":
        vals = gst["monthly_turnover_lakhs"][-12:]
        return pd.DataFrame({
            "Month": [f"M-{12-i}" for i in range(12)],
            "Turnover (₹L)": vals,
        })
    if metric_key == "abb":
        vals = aa["monthly_closing_balance_lakhs"][-6:]
        return pd.DataFrame({
            "Month": [f"M-{6-i}" for i in range(6)],
            "Closing balance (₹L)": vals,
            "ABB (3M avg)": [""] * 5 + [aa["abb_lakhs"]],
        })
    if metric_key == "cibil":
        return _kv_table([
            ("CIBIL score", bureau["cibil_score"]),
            ("Active loans", bureau["active_loans"]),
            ("DPD (12M)", bureau["dpd_12m"]),
            ("Write-offs (36M)", bureau["write_offs_36m"]),
            ("Credit utilisation", f"{bureau['credit_utilization']*100:.0f}%"),
        ])
    if metric_key == "emi":
        return _kv_table([
            ("EMI on-time rate", f"{aa['emi_on_time_rate']*100:.1f}%"),
            ("Bounces (12M)", aa["bounce_count_12m"]),
            ("OD/CC utilisation", f"{aa['od_utilization']*100:.0f}%"),
            ("Avg monthly credits (₹L)", f"{avg_recent(aa['monthly_credits_lakhs'], 6):.2f}"),
            ("Avg monthly debits (₹L)", f"{avg_recent(aa['monthly_debits_lakhs'], 6):.2f}"),
        ])
    if metric_key == "employees":
        cnt = epfo["employee_count"][-12:]
        wages = epfo["monthly_wage_bill_lakhs"][-12:]
        status = epfo["contribution_status"][-12:]
        return pd.DataFrame({
            "Month": [f"M-{12-i}" for i in range(12)],
            "Headcount": cnt,
            "Wage bill (₹L)": wages,
            "EPFO status": status,
        })
    return _kv_table([("No drill-down", "—")])


METRIC_KEYS = {
    "GST compliance": "gst_compliance",
    "Monthly turnover": "turnover",
    "ABB (3M)": "abb",
    "Promoter CIBIL": "cibil",
    "EMI on-time": "emi",
    "Employees": "employees",
}


def source_snapshot_tables(profile: dict) -> dict[str, pd.DataFrame]:
    """One table per data source with actual values."""
    gst = profile["gst"]
    upi = profile["upi"]
    aa = profile["aa"]
    epfo = profile["epfo"]
    google = profile["google"]
    bureau = profile["bureau"]
    courts = profile["courts"]
    elec = profile["electricity"]
    inv = profile["investment"]
    news = profile.get("news", {})

    n = len(gst["monthly_turnover_lakhs"])
    months = [f"M{i+1}" for i in range(n)]

    lb = profile.get("loan_book", {})
    coll = profile.get("collections", {}).get("monthly_panel", [])
    unstructured = profile.get("unstructured", {})

    tables = {
        "Loan tape": _kv_table([
            ("Loan ID", lb.get("loan_id", "—")),
            ("Type", lb.get("loan_type", "—")),
            ("Sanctioned (₹L)", lb.get("sanctioned_amount_lakhs", "—")),
            ("Outstanding (₹L)", lb.get("outstanding_lakhs", "—")),
            ("EMI (₹L)", lb.get("monthly_emi_lakhs", "—")),
        ]),
        "Collections": pd.DataFrame(coll) if coll else _kv_table([("Status", "No panel")]),
        "GST": pd.DataFrame({
            "Month": months,
            "Turnover (₹L)": gst["monthly_turnover_lakhs"],
            "Filing": gst["filing_status"],
        }),
        "UPI": pd.DataFrame({
            "Month": [f"M{i+1}" for i in range(len(upi["monthly_volume_lakhs"]))],
            "Volume (₹L)": upi["monthly_volume_lakhs"],
            "Avg ticket (₹)": upi["avg_ticket_size"],
        }),
        "Bank (AA)": pd.DataFrame({
            "Month": [f"M{i+1}" for i in range(len(aa["monthly_credits_lakhs"]))],
            "Credits (₹L)": aa["monthly_credits_lakhs"],
            "Debits (₹L)": aa["monthly_debits_lakhs"],
            "Balance (₹L)": aa["monthly_closing_balance_lakhs"],
        }),
        "EPFO": pd.DataFrame({
            "Month": [f"M{i+1}" for i in range(len(epfo["employee_count"]))],
            "Employees": epfo["employee_count"],
            "Wage bill (₹L)": epfo["monthly_wage_bill_lakhs"],
            "Status": epfo["contribution_status"],
        }),
        "Electricity": pd.DataFrame({
            "Month": [f"M{i+1}" for i in range(len(elec["monthly_kwh"]))],
            "kWh": elec["monthly_kwh"],
        }),
        "Courts": _kv_table([
            ("Active litigation", active_litigation_label(profile)),
            ("Civil cases", courts["civil_cases"]),
            ("Criminal cases", courts["criminal_cases"]),
            ("Insolvency", courts["insolvency_petitions"]),
            ("Outstanding (₹L)", courts["total_outstanding_litigation_lakhs"]),
        ]),
        "Google": _kv_table([
            ("Rating", f"{google['rating']} ★"),
            ("Reviews", google["review_count"]),
            ("Response rate", f"{google['response_rate']*100:.0f}%"),
            ("Velocity 6M", google["review_velocity_6m"]),
        ]),
        "Investment": _kv_table([
            ("CapEx 12M (₹L)", inv["capex_lakhs_12m"]),
            ("R&D annual (₹L)", inv["rnd_spend_lakhs_annual"]),
            ("Patents", inv["patents_count"]),
            ("Govt scheme", "Yes" if inv["govt_scheme_beneficiary"] else "No"),
        ]),
        "Macro": _kv_table([
            ("Sector growth", f"{SECTOR_GROWTH.get(profile['sector'], 5):.1f}%"),
            ("Repo rate", f"{MACRO_INDICATORS['repo_rate']}%"),
            ("Monsoon index", f"{profile['macro'].get('monsoon_index_pct', 100)}%"),
            ("Region", profile["macro"].get("region_tier", "—")),
        ]),
        "News": pd.DataFrame([
            {
                "Headline": a.get("title", ""),
                "Sentiment": a.get("sentiment", "neutral"),
                "Source": a.get("source", ""),
                "Days ago": a.get("published_days_ago", "—"),
            }
            for a in news.get("articles", [])
        ]) if news.get("articles") else _kv_table([("Status", "No articles")]),
        "Bureau": _kv_table([
            ("Promoter", bureau["promoter_name"]),
            ("NTC", "Yes" if bureau.get("is_ntc") else "No"),
            ("CIBIL", bureau["cibil_score"] if not bureau.get("is_ntc") else "N/A (NTC)"),
            ("Other loans", len(bureau.get("other_loans", []))),
            ("DPD 12M", bureau["dpd_12m"]),
            ("Write-offs 36M", bureau["write_offs_36m"]),
            ("Utilisation", f"{bureau['credit_utilization']*100:.0f}%"),
        ]),
        "Unstructured": pd.DataFrame([
            {"Type": "news", "Text": n.get("headline", ""), "Days ago": n.get("days_ago")}
            for n in unstructured.get("news_mentions", [])
        ] + [
            {"Type": "rm_note", "Text": n.get("text", ""), "Days ago": n.get("days_ago")}
            for n in unstructured.get("rm_call_notes", [])
        ]) if unstructured else _kv_table([("Status", "None")]),
    }
    return tables


def score_summary_table(result: dict) -> pd.DataFrame:
    if "stress_prob" in result:
        rows = [
            (FINN_SCORE_LABEL, f"{result['stress_prob']*100:.1f}%"),
            ("Risk band", result.get("band", "—")),
            ("Rule component", f"{result.get('rule_stress_prob', 0)*100:.1f}%"),
            ("ML component (full)", f"{result.get('ml_stress_prob', 0)*100:.1f}%" if result.get("ml_stress_prob") else "—"),
            ("ML component (structured)", f"{result.get('structured_ml_prob', 0)*100:.1f}%" if result.get("structured_ml_prob") else "—"),
            ("Horizon", f"{result.get('horizon_months', 12)} months"),
        ]
        for pillar, data in result.get("pillars", {}).items():
            rows.append((f"Pillar: {pillar.replace('_', ' ').title()}", f"{data['score']:.0f}/100"))
        return _kv_table(rows, columns=("Metric", "Value"))

    rows = [
        (FINN_SCORE_LABEL, int(result.get("final_score", 0))),
        ("Rule component", int(result.get("rule_score", 0))),
        ("ML component", int(result["ml_score"]) if result.get("ml_score") else "—"),
    ]
    for pillar, data in result.get("pillars", {}).items():
        rows.append((f"Pillar: {pillar.title()}", f"{data['score']:.0f}/100"))
    return _kv_table(rows, columns=("Metric", "Value"))
