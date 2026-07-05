"""Open-Meteo public weather API — rainfall proxy for agri / regional context."""

from __future__ import annotations

import logging
from functools import lru_cache

import requests

logger = logging.getLogger(__name__)

CITY_COORDS = {
    "Pune": (18.52, 73.86),
    "Ahmedabad": (23.02, 72.57),
    "Delhi": (28.61, 77.21),
    "Nagpur": (21.15, 79.09),
    "Mumbai": (19.08, 72.88),
    "Bengaluru": (12.97, 77.59),
    "Chennai": (13.08, 80.27),
    "Kolkata": (22.57, 88.36),
    "Hyderabad": (17.39, 78.49),
    "Jaipur": (26.91, 75.79),
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@lru_cache(maxsize=32)
def fetch_live_weather(city: str) -> dict:
    """30-day precipitation sum; monsoon_index_pct vs nominal 100mm baseline."""
    lat, lon = CITY_COORDS.get(city, (20.59, 78.96))  # India centroid fallback
    result = {
        "live": False,
        "city": city,
        "source": "mock",
        "monsoon_index_pct": 100.0,
        "precipitation_mm_30d": None,
        "fetched_from": None,
    }

    try:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "precipitation_sum",
            "past_days": 30,
            "forecast_days": 1,
            "timezone": "Asia/Kolkata",
        }
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        resp.raise_for_status()
        daily = resp.json().get("daily", {})
        precip = daily.get("precipitation_sum", [])
        total = sum(p or 0 for p in precip)
        # Normalise: 80–120mm / 30d as 80–120% index (rough agri proxy)
        index = min(130, max(70, (total / 100.0) * 100))
        result.update({
            "live": True,
            "source": "open-meteo.com",
            "precipitation_mm_30d": round(total, 1),
            "monsoon_index_pct": round(index, 1),
            "fetched_from": OPEN_METEO_URL,
        })
    except Exception as exc:
        logger.warning("Live weather fetch failed for %s: %s", city, exc)

    return result
