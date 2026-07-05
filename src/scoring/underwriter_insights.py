"""Underwriter-facing insights derived from features and profile."""

from __future__ import annotations

from src.utils.helpers import score_to_grade


def get_credit_decision(score: float) -> dict:
    if score >= 700:
        return {
            "action": "APPROVE",
            "color": "green",
            "headline": "Eligible for unsecured MSME working-capital limit",
            "rationale": "Strong alt-data footprint across revenue, liquidity, and promoter quality.",
        }
    if score >= 550:
        return {
            "action": "REVIEW",
            "color": "orange",
            "headline": "Approve with conditions or reduced limit",
            "rationale": "Mixed signals — manual review recommended on weak pillars.",
        }
    return {
        "action": "DECLINE",
        "color": "red",
        "headline": "Not recommended for unsecured credit",
        "rationale": "Material compliance, liquidity, or governance concerns identified.",
    }


def get_risk_flags(features: dict, profile: dict) -> list[dict]:
    flags = []
    courts = profile["courts"]
    gst = profile["gst"]

    if features["gst_filing_compliance"] < 0.85:
        flags.append({"level": "red", "label": "GST filing irregular", "detail": f"{features['gst_filing_compliance']*100:.0f}% compliance"})
    elif features["gst_payment_delays"] > 2:
        flags.append({"level": "amber", "label": "GST payment delays", "detail": f"{int(features['gst_payment_delays'])} delayed periods"})

    if features["aa_bounce_count"] > 0:
        flags.append({"level": "red", "label": "EMI / cheque bounces", "detail": f"{int(features['aa_bounce_count'])} in 12M"})
    elif features["aa_emi_on_time_rate"] < 0.9:
        flags.append({"level": "amber", "label": "EMI discipline weak", "detail": f"{features['aa_emi_on_time_rate']*100:.0f}% on-time"})

    if courts["civil_cases"] + courts["criminal_cases"] + courts["insolvency_petitions"] > 0:
        flags.append({
            "level": "red",
            "label": "Active litigation",
            "detail": f"{courts['civil_cases']} civil · {courts['criminal_cases']} criminal",
        })

    if features["gst_turnover_yoy_growth"] > 10:
        flags.append({"level": "green", "label": "Revenue growth", "detail": f"+{features['gst_turnover_yoy_growth']:.1f}% YoY (GST)"})
    elif features["gst_turnover_yoy_growth"] < 0:
        flags.append({"level": "red", "label": "Revenue decline", "detail": f"{features['gst_turnover_yoy_growth']:.1f}% YoY (GST)"})

    if features["aa_abb_lakhs"] >= 5:
        flags.append({"level": "green", "label": "Healthy ABB", "detail": f"₹{features['aa_abb_lakhs']:.1f}L (3M avg)"})

    if features["epfo_contribution_compliance"] >= 0.9:
        flags.append({"level": "green", "label": "Payroll compliance", "detail": "EPFO contributions regular"})

    if features["google_rating"] >= 4.0:
        flags.append({"level": "green", "label": "Customer sentiment", "detail": f"{features['google_rating']:.1f}★ Google rating"})

    # Promoter bureau — lowest priority for NTC MSME underwriting
    if features["promoter_cibil"] < 650:
        flags.append({"level": "red", "label": "Weak promoter bureau", "detail": f"CIBIL {int(features['promoter_cibil'])}"})
    elif features["promoter_cibil"] >= 750:
        flags.append({"level": "green", "label": "Strong promoter bureau", "detail": f"CIBIL {int(features['promoter_cibil'])}"})

    return flags


def get_key_metrics(features: dict, profile: dict) -> list[dict]:
    return [
        {"label": "GST compliance", "value": f"{features['gst_filing_compliance']*100:.0f}%", "benchmark": "≥ 90%"},
        {"label": "Monthly turnover", "value": f"₹{features['gst_avg_monthly_turnover']:.1f}L", "benchmark": "Sector median"},
        {"label": "ABB (3M)", "value": f"₹{features['aa_abb_lakhs']:.1f}L", "benchmark": "≥ ₹3L"},
        {"label": "EMI on-time", "value": f"{features['aa_emi_on_time_rate']*100:.0f}%", "benchmark": "≥ 95%"},
        {"label": "Employees", "value": str(int(features["epfo_headcount"])), "benchmark": "Stable trend"},
        {"label": "Promoter CIBIL", "value": str(int(features["promoter_cibil"])), "benchmark": "≥ 700"},
    ]


def get_traditional_gap(profile: dict, score: float) -> dict:
    """What traditional underwriting would miss vs alt-data."""
    return {
        "traditional": "REJECT / NO FILE",
        "traditional_reason": "No audited financials · Thin/no commercial bureau · Informal books",
        "alt_data": f"SCORE {int(score)} · {score_to_grade(score)}",
        "alt_reason": "Digital footprint validates business activity and cash behaviour",
        "sources_used": 10,
        "time_to_decision": "< 5 min",
    }


def get_demo_preview(msme_id: str, features: dict, profile: dict, score: float) -> dict:
    meta = {
        "MSME001": {"tag": "Strong NTC candidate", "type": "Manufacturer"},
        "MSME002": {"tag": "High UPI velocity retail", "type": "Retail"},
        "MSME003": {"tag": "Multiple red flags", "type": "Trader"},
        "MSME004": {"tag": "Sector + weather tailwind", "type": "Agri-input"},
    }.get(msme_id, {"tag": "Sample case", "type": "MSME"})

    return {
        "msme_id": msme_id,
        "score": int(score),
        "grade": score_to_grade(score),
        "decision": get_credit_decision(score)["action"],
        "tag": meta["tag"],
        "type": meta["type"],
        "turnover": f"₹{features['gst_avg_monthly_turnover']:.1f}L/mo",
        "cibil": int(features["promoter_cibil"]),
        "gst_compliance": f"{features['gst_filing_compliance']*100:.0f}%",
        "litigation": profile["courts"]["civil_cases"] + profile["courts"]["criminal_cases"],
    }
