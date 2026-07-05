"""Stress prediction package."""

from src.prediction import stress_insights
from src.prediction.stress_insights import (
    get_key_metrics,
    get_risk_flags,
    get_stress_decision,
    stress_to_band,
)

get_payment_metrics = getattr(stress_insights, "get_payment_metrics", None)
get_facility_metrics = getattr(stress_insights, "get_facility_metrics", None)

__all__ = [
    "get_facility_metrics",
    "get_key_metrics",
    "get_payment_metrics",
    "get_risk_flags",
    "get_stress_decision",
    "stress_insights",
    "stress_to_band",
]
