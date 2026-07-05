"""Merge live public data into MSME profile; track source status."""

from __future__ import annotations

import copy

from src.connectors.live.google_places import fetch_google_places
from src.connectors.live.macro_public import fetch_live_macro
from src.connectors.live.weather_public import fetch_live_weather
from src.utils.constants import MACRO_INDICATORS, SECTOR_GROWTH


def enrich_profile_with_public_data(profile: dict) -> tuple[dict, list[dict]]:
    """
    Overlay live public data where available.
    Returns (enriched_profile, source_status_list).
    """
    enriched = copy.deepcopy(profile)
    status: list[dict] = []

    # --- Macro (public RBI snapshot) ---
    live_macro = fetch_live_macro()
    enriched["macro"] = dict(enriched.get("macro", {}))
    if live_macro.get("live"):
        enriched["macro"]["repo_rate_live"] = live_macro["repo_rate"]
        enriched["macro"]["inflation_cpi_live"] = live_macro.get("inflation_cpi")
        enriched["macro"]["rbi_stance"] = live_macro.get("stance")
        enriched["macro"]["macro_fetch_source"] = live_macro["source"]
    enriched["macro"]["sector_growth_pct"] = SECTOR_GROWTH.get(profile["sector"], 5.0)

    status.append({
        "key": "macro",
        "name": "Macro / RBI",
        "mode": "live" if live_macro.get("live") else "static",
        "detail": f"Repo {live_macro['repo_rate']}%"
        + (f" · {live_macro.get('stance', '')}" if live_macro.get("stance") else "")
        + (f" · via {live_macro['source']}" if live_macro.get("live") else " · static constants"),
    })

    # --- Weather (Open-Meteo) ---
    live_weather = fetch_live_weather(profile.get("city", "Pune"))
    if live_weather.get("live"):
        enriched["macro"]["monsoon_index_pct"] = live_weather["monsoon_index_pct"]
        enriched["macro"]["precipitation_mm_30d"] = live_weather["precipitation_mm_30d"]
        enriched["macro"]["weather_source"] = live_weather["source"]
        weather_mode = "live"
        weather_detail = f"{live_weather['precipitation_mm_30d']}mm / 30d · index {live_weather['monsoon_index_pct']}%"
    else:
        weather_mode = "mock"
        weather_detail = "Synthetic monsoon index (API unavailable)"

    status.append({
        "key": "weather",
        "name": "Weather / Rainfall",
        "mode": weather_mode,
        "detail": weather_detail,
    })

    # --- Google Places (optional API key) ---
    google_live = fetch_google_places(profile["business_name"], profile.get("city", ""))
    if google_live:
        enriched["google"] = {**enriched["google"], **google_live}
        status.append({
            "key": "google",
            "name": "Google Business",
            "mode": "live",
            "detail": f"{google_live['rating']}★ · {google_live['review_count']} reviews (Places API)",
        })
    else:
        status.append({
            "key": "google",
            "name": "Google Business",
            "mode": "mock",
            "detail": "Synthetic reviews · set GOOGLE_PLACES_API_KEY for live",
        })

    # --- Borrower-specific sources (mock in PoC) ---
    mock_sources = [
        ("gst", "GST Returns", "GSP / GSTN API — see docs/CONNECTOR_INTEGRATION.md"),
        ("upi", "UPI Merchant", "Bank / NPCI merchant API"),
        ("aa", "Account Aggregator", "RBI AA framework (FIU consent)"),
        ("epfo", "EPFO", "Employer establishment API"),
        ("bureau", "Promoter Bureau", "CIBIL / CRIF commercial API"),
        ("courts", "Court Records", "eCourts aggregator"),
        ("electricity", "Electricity", "Discom API or bill OCR"),
        ("investment", "Investment / MCA", "MCA21 / patent registry"),
    ]
    for key, name, hint in mock_sources:
        status.append({"key": key, "name": name, "mode": "mock", "detail": hint})

    return enriched, status


def get_live_macro_for_display() -> dict:
    """Expose live macro for UI without full profile."""
    return fetch_live_macro()
