"""Optional Google Places API — requires GOOGLE_PLACES_API_KEY."""

from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger(__name__)

PLACES_TEXT_SEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
PLACES_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"


def fetch_google_places(business_name: str, city: str) -> dict | None:
    api_key = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("STREAMLIT_GOOGLE_PLACES_API_KEY")
    if not api_key:
        return None

    query = f"{business_name} {city}"
    try:
        search = requests.get(
            PLACES_TEXT_SEARCH,
            params={"query": query, "key": api_key},
            timeout=10,
        )
        search.raise_for_status()
        results = search.json().get("results", [])
        if not results:
            return None

        place_id = results[0]["place_id"]
        details = requests.get(
            PLACES_DETAILS,
            params={
                "place_id": place_id,
                "fields": "name,rating,user_ratings_total,reviews",
                "key": api_key,
            },
            timeout=10,
        )
        details.raise_for_status()
        place = details.json().get("result", {})

        reviews = []
        for r in place.get("reviews", [])[:10]:
            text = r.get("text", "")
            rating = r.get("rating", 3)
            sentiment = "positive" if rating >= 4 else "negative" if rating <= 2 else "neutral"
            reviews.append({
                "rating": rating,
                "text": text[:200],
                "sentiment": sentiment,
                "days_ago": 30,
            })

        return {
            "live": True,
            "source": "google_places_api",
            "place_id": place_id,
            "rating": place.get("rating", 0),
            "review_count": place.get("user_ratings_total", 0),
            "reviews": reviews or [{"rating": 3, "text": "No review text", "sentiment": "neutral", "days_ago": 0}],
            "response_rate": 0.5,
            "review_velocity_6m": min(10, len(reviews)),
            "fetched_from": "Google Places API",
        }
    except Exception as exc:
        logger.warning("Google Places fetch failed: %s", exc)
        return None
