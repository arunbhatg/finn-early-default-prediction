"""Stress insights for RM / collections workflow."""

from __future__ import annotations

from src.utils.constants import STRESS_BANDS


def stress_to_band(prob: float) -> dict:
    for threshold, label, color in STRESS_BANDS:
        if prob >= threshold:
            return {"band": label, "color": color, "threshold": threshold}
    return {"band": "Low", "color": "#166534", "threshold": 0.0}


def get_stress_decision(stress_prob: float) -> dict:
    band = stress_to_band(stress_prob)
    actions = {
        "Critical": ("ESCALATE", "Immediate collections review — restructure or recovery action"),
        "High": ("INTERVENE", "RM field visit + payment plan within 7 days"),
        "Watch": ("MONITOR", "Enhanced monitoring — weekly payment tracking"),
        "Low": ("ROUTINE", "Standard quarterly review — no immediate action"),
    }
    action, headline = actions.get(band["band"], actions["Low"])
    return {"action": action, "headline": headline, "band": band["band"], "color": band["color"]}


def get_key_metrics(features: dict, profile: dict) -> list[dict]:
    bureau = profile.get("bureau", {})
    loan = profile.get("loan_book", {})
    is_ntc = bureau.get("is_ntc", False)

    metrics = [
        {"label": "12m stress probability", "value": f"{features.get('_stress_prob_display', 0)*100:.0f}%"},
        {"label": "EMI on-time (6m)", "value": f"{features.get('emi_on_time_rate_6m', 0)*100:.0f}%"},
        {"label": "Max DPD (6m)", "value": f"{features.get('dpd_max_6m', 0)} days"},
        {"label": "Loan type", "value": loan.get("loan_type", "—")},
        {"label": "Outstanding", "value": f"₹{loan.get('outstanding_lakhs', 0):.1f}L"},
    ]

    if is_ntc:
        metrics.append({"label": "Credit file", "value": "NTC — alt-data"})
        metrics.append({"label": "GST compliance", "value": f"{features.get('ntc_gst_compliance_proxy', 0)*100:.0f}%"})
    else:
        metrics.append({"label": "Promoter CIBIL", "value": str(int(bureau.get("cibil_score", 0)))})
        metrics.append({"label": "Other-loan on-time", "value": f"{features.get('bureau_other_emi_on_time_rate', 0)*100:.0f}%"})

    return metrics


def get_risk_flags(features: dict, profile: dict) -> list[dict]:
    flags = []

    if features.get("dpd_max_6m", 0) >= 15:
        flags.append({"level": "red", "label": f"DPD spike ({features['dpd_max_6m']}d)"})
    elif features.get("dpd_max_6m", 0) >= 5:
        flags.append({"level": "amber", "label": "Payment delays emerging"})

    if features.get("bounce_count_6m", 0) >= 2:
        flags.append({"level": "red", "label": "Multiple EMI bounces"})
    if features.get("ptp_broken_count_6m", 0) >= 1:
        flags.append({"level": "amber", "label": "Broken promise-to-pay"})

    if features.get("bureau_other_max_dpd_12m", 0) >= 30:
        flags.append({"level": "red", "label": "DPD on other bureau loans"})

    if features.get("composite_text_stress_score", 0) >= 0.4:
        flags.append({"level": "amber", "label": "Negative unstructured signals"})

    if features.get("is_ntc") and features.get("ntc_gst_compliance_proxy", 1) < 0.8:
        flags.append({"level": "amber", "label": "NTC — GST filing gaps"})

    if features.get("emi_on_time_rate_6m", 0) >= 0.95:
        flags.append({"level": "green", "label": "Strong payment timing"})
    if features.get("is_ntc") and features.get("ntc_upi_volume_stability", 0) >= 0.7:
        flags.append({"level": "green", "label": "NTC — stable UPI collections"})

    if not flags:
        flags.append({"level": "green", "label": "No immediate flags"})

    return flags
