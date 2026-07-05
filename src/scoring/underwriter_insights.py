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

    if features["gst_filing_compliance"] < 0.85:
        flags.append({"level": "red", "label": "GST filing irregular", "detail": f"{features['gst_filing_compliance']*100:.0f}% compliance"})
    elif features["gst_payment_delays"] > 0:
        flags.append({
            "level": "amber" if features["gst_payment_delays"] <= 2 else "red",
            "label": "GST late penalties",
            "detail": f"{int(features['gst_payment_delays'])} delayed filings",
        })

    if features["aa_bounce_count"] > 0:
        flags.append({"level": "red", "label": "Autopay / cheque failures", "detail": f"{int(features['aa_bounce_count'])} in 12M"})
    elif features["aa_emi_on_time_rate"] < 0.9:
        flags.append({"level": "amber", "label": "Bill pay discipline weak", "detail": f"{features['aa_emi_on_time_rate']*100:.0f}% on-time"})

    if features["electricity_payment_regularity"] < 0.85:
        flags.append({"level": "red", "label": "Utility bill delays", "detail": f"{features['electricity_payment_regularity']*100:.0f}% paid on time"})
    elif features["electricity_payment_regularity"] >= 0.95:
        flags.append({"level": "green", "label": "Bills paid on time", "detail": f"Electricity {features['electricity_payment_regularity']*100:.0f}% regular"})

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

    if features["epfo_headcount_growth"] > 5:
        flags.append({"level": "green", "label": "Employee growth", "detail": f"+{features['epfo_headcount_growth']:.1f}% YoY"})
    elif features["epfo_headcount_growth"] < -3:
        flags.append({"level": "red", "label": "Headcount shrinking", "detail": f"{features['epfo_headcount_growth']:.1f}% YoY"})

    if features["google_rating"] >= 4.0:
        flags.append({"level": "green", "label": "Google business sentiment", "detail": f"{features['google_rating']:.1f}★ · {features['google_sentiment_score']*100:.0f}% positive"})
    elif features["google_rating"] < 3.5:
        flags.append({"level": "amber", "label": "Weak Google sentiment", "detail": f"{features['google_rating']:.1f}★ rating"})

    return flags


def get_key_metrics(features: dict, profile: dict) -> list[dict]:
    growth = features["gst_turnover_yoy_growth"]
    growth_sign = "+" if growth >= 0 else ""
    return [
        {"label": "GST YoY growth", "value": f"{growth_sign}{growth:.1f}%"},
        {"label": "GST compliance", "value": f"{features['gst_filing_compliance']*100:.0f}%"},
        {"label": "Bill pay on-time", "value": f"{features['electricity_payment_regularity']*100:.0f}%"},
        {"label": "Autopay failures", "value": str(int(features["aa_bounce_count"]))},
        {"label": "Late penalties", "value": str(int(features["gst_payment_delays"]))},
        {"label": "Employee growth", "value": f"{features['epfo_headcount_growth']:+.1f}%"},
        {
            "label": "Google sentiment",
            "value": f"{features['google_rating']:.1f}★",
            "benchmark": f"{features['google_sentiment_score']*100:.0f}% positive",
        },
        {"label": "Monthly turnover", "value": f"₹{features['gst_avg_monthly_turnover']:.1f}L"},
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
