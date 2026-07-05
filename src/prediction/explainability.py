"""Stress prediction explainability."""

from __future__ import annotations

from src.utils.constants import PILLAR_WEIGHTS


FACTOR_SOURCE = {
    "EMI": "collections",
    "DPD": "collections",
    "Payment": "collections",
    "Bureau": "bureau",
    "CIBIL": "bureau",
    "Other-loan": "bureau",
    "NTC": "bureau",
    "Collection": "collections",
    "Cashflow": "aa",
    "GST": "gst",
    "text stress": "google",
    "News": "google",
    "RM": "google",
    "Google": "google",
    "Sector": "macro",
    "Monsoon": "macro",
}


def _source_for_factor(factor: str) -> str:
    for prefix, source in FACTOR_SOURCE.items():
        if prefix.lower() in factor.lower():
            return source
    return "other"


def extract_stress_drivers(pillars: dict) -> dict:
    all_drivers = []
    for pillar, data in pillars.items():
        for d in data.get("drivers", []):
            impact = d["impact"]
            stress_pts = -impact if impact > 50 else (50 - impact) * 0.5
            all_drivers.append(
                {
                    "factor": d["factor"],
                    "value": d["value"],
                    "pillar": pillar,
                    "source": _source_for_factor(d["factor"]),
                    "impact": impact,
                    "stress_points": round(stress_pts, 1),
                    "direction": "risk" if stress_pts > 5 else "protective",
                }
            )

    risks = sorted([d for d in all_drivers if d["stress_points"] > 5], key=lambda x: -x["stress_points"])
    protective = sorted([d for d in all_drivers if d["stress_points"] <= -3], key=lambda x: x["stress_points"])

    return {"risk_factors": risks[:5], "protective_factors": protective[:5], "all_drivers": all_drivers}


def build_stress_narrative(stress_prob: float, risk_factors: list[dict], protective_factors: list[dict]) -> str:
    pct = int(stress_prob * 100)
    top_risk = risk_factors[0]["factor"] if risk_factors else "no dominant risk signal"
    top_protect = protective_factors[0]["factor"] if protective_factors else "consistent payment history"

    if stress_prob >= 0.70:
        return f"**Critical** — {pct}% stress probability in next 12 months. Primary driver: {top_risk}."
    if stress_prob >= 0.45:
        return f"**High watch** — {pct}% stress probability. Key concern: {top_risk}. Offset: {top_protect}."
    if stress_prob >= 0.25:
        return f"**Watch list** — {pct}% stress probability. Monitor {top_risk}; supported by {top_protect}."
    return f"**Low risk** — {pct}% stress probability. Protective signal: {top_protect}."
