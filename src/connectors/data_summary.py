"""Human-readable summary of data pulled from each alternative source."""

from __future__ import annotations

from src.utils.constants import MACRO_INDICATORS, SECTOR_GROWTH
from src.utils.helpers import avg_recent, compliance_rate, yoy_growth


def _months_label(n: int) -> str:
    return f"{n} months"


def summarize_gst(gst: dict) -> dict:
    turnover = gst["monthly_turnover_lakhs"]
    compliance = compliance_rate(gst["filing_status"], {"filed"})
    return {
        "source": "GST",
        "icon": "📋",
        "records": _months_label(len(turnover)),
        "headline": f"Avg monthly turnover ₹{avg_recent(turnover, 6):.1f}L",
        "highlights": [
            f"GSTR filings: {compliance*100:.0f}% on-time ({len(turnover)} months)",
            f"Turnover YoY growth: {yoy_growth(turnover):+.1f}%",
            f"B2B sales ratio: {gst['b2b_sales_ratio']*100:.0f}%",
            f"Payment delays: {gst['payment_delays_count']} instances",
        ],
        "status": "healthy" if compliance >= 0.9 and gst["payment_delays_count"] <= 1 else "warning",
    }


def summarize_upi(upi: dict) -> dict:
    vol = upi["monthly_volume_lakhs"]
    return {
        "source": "UPI",
        "icon": "📱",
        "records": _months_label(len(vol)),
        "headline": f"Avg monthly UPI volume ₹{avg_recent(vol, 6):.1f}L",
        "highlights": [
            f"VPA: {upi['vpa']}",
            f"Volume YoY growth: {yoy_growth(vol):+.1f}%",
            f"Merchant (P2M) ratio: {upi['p2m_ratio']*100:.0f}%",
            f"Failed txn rate: {upi['failed_txn_rate']*100:.2f}%",
        ],
        "status": "healthy" if upi["failed_txn_rate"] < 0.025 else "warning",
    }


def summarize_aa(aa: dict) -> dict:
    return {
        "source": "Account Aggregator",
        "icon": "🏦",
        "records": _months_label(len(aa["monthly_credits_lakhs"])),
        "headline": f"ABB ₹{aa['abb_lakhs']}L · EMI on-time {aa['emi_on_time_rate']*100:.0f}%",
        "highlights": [
            f"Bank accounts: {len(aa['accounts'])} ({', '.join(a['bank'] for a in aa['accounts'])})",
            f"Avg monthly credits: ₹{avg_recent(aa['monthly_credits_lakhs'], 6):.1f}L",
            f"Cheque/EMI bounces (12M): {aa['bounce_count_12m']}",
            f"OD/CC utilization: {aa['od_utilization']*100:.0f}%",
        ],
        "status": "healthy" if aa["bounce_count_12m"] == 0 and aa["emi_on_time_rate"] >= 0.9 else "warning",
    }


def summarize_epfo(epfo: dict) -> dict:
    compliance = compliance_rate(epfo["contribution_status"], {"paid"})
    return {
        "source": "EPFO",
        "icon": "👥",
        "records": _months_label(len(epfo["employee_count"])),
        "headline": f"{epfo['employee_count'][-1]} employees · wage bill ₹{epfo['monthly_wage_bill_lakhs'][-1]:.1f}L",
        "highlights": [
            f"Contribution compliance: {compliance*100:.0f}%",
            f"Headcount trend: {yoy_growth([float(x) for x in epfo['employee_count']]):+.1f}% YoY",
            f"New joiners (12M): {epfo['new_joiners_12m']}",
            f"Attrition rate: {epfo['attrition_rate']*100:.0f}%",
        ],
        "status": "healthy" if compliance >= 0.85 else "warning",
    }


def summarize_google(google: dict) -> dict:
    pos = sum(1 for r in google["reviews"] if r["sentiment"] == "positive")
    total = len(google["reviews"]) or 1
    live_tag = " · LIVE Places API" if google.get("live") else " · synthetic"
    return {
        "source": "Google Business",
        "icon": "⭐",
        "records": f"{google['review_count']} reviews{live_tag}",
        "headline": f"{google['rating']}★ rating · {pos/total*100:.0f}% positive sentiment",
        "highlights": [
            f"Reviews analysed (NLP): {total}",
            f"New reviews (6M): {google['review_velocity_6m']}",
            f"Owner response rate: {google['response_rate']*100:.0f}%",
            "Sentiment extracted via keyword/NLP scoring",
        ],
        "status": "healthy" if google["rating"] >= 4.0 else "warning",
    }


def summarize_bureau(bureau: dict) -> dict:
    return {
        "source": "Promoter Bureau",
        "icon": "🪪",
        "records": "36-month history",
        "headline": f"CIBIL {bureau['cibil_score']} · {bureau['promoter_name']}",
        "highlights": [
            f"Active loans: {bureau['active_loans']}",
            f"DPD (12M): {bureau['dpd_12m']}",
            f"Write-offs (36M): {bureau['write_offs_36m']}",
            f"Credit utilization: {bureau['credit_utilization']*100:.0f}%",
        ],
        "status": "healthy" if bureau["cibil_score"] >= 700 else "warning",
    }


def summarize_courts(courts: dict) -> dict:
    total = courts["civil_cases"] + courts["criminal_cases"] + courts["insolvency_petitions"]
    return {
        "source": "Court Records",
        "icon": "⚖️",
        "records": f"{total} active cases",
        "headline": "Clean record" if total == 0 else f"{total} litigation flags",
        "highlights": [
            f"Civil cases: {courts['civil_cases']}",
            f"Criminal cases: {courts['criminal_cases']}",
            f"Insolvency petitions: {courts['insolvency_petitions']}",
            f"Outstanding litigation: ₹{courts['total_outstanding_litigation_lakhs']}L",
        ],
        "status": "healthy" if total == 0 else "risk",
    }


def summarize_electricity(elec: dict) -> dict:
    kwh = elec["monthly_kwh"]
    return {
        "source": "Electricity (Discom)",
        "icon": "⚡",
        "records": _months_label(len(kwh)),
        "headline": f"Avg {avg_recent(kwh, 6):,.0f} kWh/month ({elec['tariff_category']})",
        "highlights": [
            f"Consumption YoY: {yoy_growth(kwh):+.1f}%",
            f"Consumer no: {elec['consumer_number']}",
            f"Payment regularity: {elec['payment_regularity']*100:.0f}%",
            "Proxy for production / operational activity",
        ],
        "status": "healthy" if yoy_growth(kwh) >= 0 else "warning",
    }


def summarize_macro(profile: dict) -> dict:
    sector = profile["sector"]
    macro = profile["macro"]
    repo = macro.get("repo_rate_live", MACRO_INDICATORS["repo_rate"])
    repo_label = f"{repo}%"
    if macro.get("macro_fetch_source"):
        repo_label += f" (live · {macro['macro_fetch_source']})"
    monsoon = macro.get("monsoon_index_pct", 100)
    monsoon_note = ""
    if macro.get("weather_source"):
        monsoon_note = f" · live rainfall {macro.get('precipitation_mm_30d')}mm/30d"
    return {
        "source": "Macro & Sector",
        "icon": "🌐",
        "records": "Live + sector static",
        "headline": f"{sector} sector growth {SECTOR_GROWTH.get(sector, 5):.1f}%",
        "highlights": [
            f"Repo rate: {repo_label}",
            f"RBI stance: {macro.get('rbi_stance', '—')}",
            f"Monsoon index: {monsoon}%{monsoon_note}",
            f"Region: {macro.get('region_tier', 'N/A')}",
        ],
        "status": "healthy",
    }


def summarize_investment(inv: dict) -> dict:
    return {
        "source": "Investment & R&D",
        "icon": "📈",
        "records": "12-month window",
        "headline": f"CapEx ₹{inv['capex_lakhs_12m']}L · R&D ₹{inv['rnd_spend_lakhs_annual']}L",
        "highlights": [
            f"Patents: {inv['patents_count']}",
            f"Govt scheme beneficiary: {'Yes' if inv['govt_scheme_beneficiary'] else 'No'}",
            "CapEx signals expansion capacity",
            "R&D indicates innovation / export potential",
        ],
        "status": "healthy" if inv["capex_lakhs_12m"] > 2 else "neutral",
    }


SUMMARIZERS = {
    "gst": lambda p: summarize_gst(p["gst"]),
    "upi": lambda p: summarize_upi(p["upi"]),
    "aa": lambda p: summarize_aa(p["aa"]),
    "epfo": lambda p: summarize_epfo(p["epfo"]),
    "google": lambda p: summarize_google(p["google"]),
    "bureau": lambda p: summarize_bureau(p["bureau"]),
    "courts": lambda p: summarize_courts(p["courts"]),
    "electricity": lambda p: summarize_electricity(p["electricity"]),
    "macro": summarize_macro,
    "investment": lambda p: summarize_investment(p["investment"]),
}


def build_data_pull_summary(profile: dict, sources: list[str] | None = None) -> list[dict]:
    sources = sources or list(SUMMARIZERS.keys())
    summaries = []
    for key in sources:
        if key in SUMMARIZERS:
            summaries.append({"key": key, **SUMMARIZERS[key](profile)})
    return summaries
