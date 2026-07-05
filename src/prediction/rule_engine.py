"""Early-warning rule engine — repayment, cashflow, bureau/NTC, NLP, context."""

from __future__ import annotations

from src.utils.helpers import clamp


def _scale(value: float, lo: float, hi: float, invert: bool = False) -> float:
    if hi == lo:
        return 50.0
    raw = clamp((value - lo) / (hi - lo) * 100, 0, 100)
    return 100 - raw if invert else raw


def score_repayment(f: dict) -> tuple[float, list[dict]]:
    """Collection payment timing and EMI discipline."""
    signals = [
        ("EMI on-time rate (6m)", _scale(f.get("emi_on_time_rate_6m", 1), 0.5, 1.0), f"{f.get('emi_on_time_rate_6m', 1)*100:.0f}%"),
        ("Max DPD last 6m (inverse)", _scale(f.get("dpd_max_6m", 0), 0, 45, invert=True), str(int(f.get("dpd_max_6m", 0)))),
        ("Payment lead days", _scale(f.get("avg_payment_lead_days", 3), 0, 5), f"{f.get('avg_payment_lead_days', 0):.1f}d"),
        ("Bureau other-loan on-time rate", _scale(f.get("bureau_other_emi_on_time_rate", 1), 0.5, 1.0), f"{f.get('bureau_other_emi_on_time_rate', 1)*100:.0f}%"),
    ]
    score = sum(s[1] for s in signals) / len(signals)
    penalties = (
        f.get("bounce_count_6m", 0) * 10
        + f.get("missed_emi_count_6m", 0) * 12
        + f.get("ptp_broken_count_6m", 0) * 8
        + f.get("bureau_other_max_dpd_12m", 0) * 0.5
    )
    score = clamp(100 - penalties, 0, 100) if penalties else score
    drivers = [{"factor": s[0], "impact": s[1], "value": s[2]} for s in signals]
    if penalties:
        drivers.append({"factor": "Collection penalty (bounce/PTP/DPD)", "impact": -penalties, "value": f"-{penalties:.0f}"})
    return score, drivers


def score_cashflow(f: dict) -> tuple[float, list[dict]]:
    signals = [
        ("Cashflow surplus ratio", _scale(f.get("aa_cashflow_surplus_ratio", 0), -0.2, 0.3), f"{f.get('aa_cashflow_surplus_ratio', 0):.2f}"),
        ("GST turnover growth", _scale(f.get("gst_turnover_yoy_growth", 0), -10, 25), f"{f.get('gst_turnover_yoy_growth', 0):.1f}%"),
        ("Utilization ratio (inverse)", _scale(f.get("utilization_ratio", 0.5), 0.3, 0.95, invert=True), f"{f.get('utilization_ratio', 0)*100:.0f}%"),
        ("EMI burden ratio (inverse)", _scale(f.get("emi_burden_ratio", 0.3), 0.1, 0.6, invert=True), f"{f.get('emi_burden_ratio', 0):.2f}"),
    ]
    decline_penalty = (f.get("gst_turnover_decline_6m", 0) + f.get("cashflow_surplus_decline", 0)) * 30
    score = clamp(sum(s[1] for s in signals) / len(signals) - decline_penalty, 0, 100)
    drivers = [{"factor": s[0], "impact": s[1], "value": s[2]} for s in signals]
    return score, drivers


def score_bureau_ntc(f: dict) -> tuple[float, list[dict]]:
    is_ntc = f.get("is_ntc", 0)
    if is_ntc:
        signals = [
            ("NTC GST compliance proxy", f.get("ntc_gst_compliance_proxy", 0) * 100, f"{f.get('ntc_gst_compliance_proxy', 0)*100:.0f}%"),
            ("NTC UPI stability proxy", f.get("ntc_upi_volume_stability", 0) * 100, f"{f.get('ntc_upi_volume_stability', 0)*100:.0f}%"),
            ("EPFO contribution compliance", f.get("epfo_contribution_compliance", 0) * 100, f"{f.get('epfo_contribution_compliance', 0)*100:.0f}%"),
        ]
    else:
        bureau_pts = _scale(f.get("promoter_cibil", 650), 550, 850)
        signals = [
            ("Promoter CIBIL", bureau_pts, str(int(f.get("promoter_cibil", 0)))),
            ("Other-loan avg DPD (inverse)", _scale(f.get("bureau_other_avg_dpd", 0), 0, 30, invert=True), f"{f.get('bureau_other_avg_dpd', 0):.1f}d"),
            ("Credit utilization (inverse)", 100 - f.get("promoter_credit_utilization", 0) * 100, f"{f.get('promoter_credit_utilization', 0)*100:.0f}%"),
        ]
    court_penalty = f.get("court_civil_cases", 0) * 8 + f.get("court_insolvency", 0) * 25
    score = clamp(sum(s[1] for s in signals) / len(signals) - court_penalty, 0, 100)
    drivers = [{"factor": s[0], "impact": s[1], "value": s[2]} for s in signals]
    return score, drivers


def score_reputation_nlp(f: dict) -> tuple[float, list[dict]]:
    text_stress = f.get("composite_text_stress_score", 0)
    signals = [
        ("Composite text stress (inverse)", _scale(text_stress, 0, 0.8, invert=True), f"{text_stress*100:.0f}%"),
        ("RM escalation count (inverse)", _scale(f.get("rm_escalation_count_6m", 0), 0, 5, invert=True), str(int(f.get("rm_escalation_count_6m", 0)))),
        ("Google rating", _scale(f.get("google_rating", 3.5), 2.5, 5.0), f"{f.get('google_rating', 0):.1f} ★"),
        ("News stress (inverse)", _scale(f.get("news_stress_score", 0), 0, 0.8, invert=True), f"{f.get('news_stress_score', 0)*100:.0f}%"),
    ]
    score = sum(s[1] for s in signals) / len(signals)
    drivers = [{"factor": s[0], "impact": s[1], "value": s[2]} for s in signals]
    return score, drivers


def score_context(f: dict) -> tuple[float, list[dict]]:
    signals = [
        ("Sector growth", _scale(f.get("sector_growth_pct", 5), -5, 12), f"{f.get('sector_growth_pct', 0):.1f}%"),
        ("Monsoon index", _scale(f.get("monsoon_index_pct", 100), 80, 120), f"{f.get('monsoon_index_pct', 0):.1f}%"),
    ]
    score = sum(s[1] for s in signals) / len(signals)
    drivers = [{"factor": s[0], "impact": s[1], "value": s[2]} for s in signals]
    return score, drivers


def compute_rule_stress_prob(features: dict) -> dict:
    from src.utils.constants import PILLAR_WEIGHTS

    pillars = {
        "repayment": score_repayment(features),
        "cashflow": score_cashflow(features),
        "bureau_ntc": score_bureau_ntc(features),
        "reputation_nlp": score_reputation_nlp(features),
        "context": score_context(features),
    }

    health = sum(pillars[k][0] * PILLAR_WEIGHTS[k] for k in pillars)
    stress_prob = round(clamp((100 - health) / 100, 0.05, 0.95), 4)

    return {
        "rule_stress_prob": stress_prob,
        "health_score": round(health, 1),
        "pillars": {k: {"score": round(v[0], 1), "drivers": v[1]} for k, v in pillars.items()},
    }
