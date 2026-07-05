"""Commercial bureau (entity-level) features for MSME scoring."""

from __future__ import annotations


def extract_commercial_bureau_features(profile: dict) -> dict:
    bureau = profile.get("bureau", {})
    commercial = bureau.get("commercial", {})
    has_file = bool(commercial.get("has_file")) and not bureau.get("is_ntc")

    if not has_file:
        return {
            "has_commercial_bureau": 0,
            "commercial_cmr_rank": 0,
            "commercial_dpd_12m": 0,
            "commercial_max_dpd_12m": 0,
            "commercial_utilization": 0.0,
            "commercial_facility_count": 0,
            "commercial_outstanding_lakhs": 0.0,
        }

    return {
        "has_commercial_bureau": 1,
        "commercial_cmr_rank": int(commercial.get("cmr_rank", 10)),
        "commercial_dpd_12m": int(commercial.get("dpd_12m", 0)),
        "commercial_max_dpd_12m": int(commercial.get("max_dpd_12m", 0)),
        "commercial_utilization": float(commercial.get("utilization", 0)),
        "commercial_facility_count": int(commercial.get("facility_count", 0)),
        "commercial_outstanding_lakhs": float(commercial.get("total_outstanding_lakhs", 0)),
    }


COMMERCIAL_BUREAU_FEATURE_COLUMNS = [
    "has_commercial_bureau",
    "commercial_cmr_rank",
    "commercial_dpd_12m",
    "commercial_max_dpd_12m",
    "commercial_utilization",
    "commercial_facility_count",
    "commercial_outstanding_lakhs",
]
