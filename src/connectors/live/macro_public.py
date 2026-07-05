"""Fetch public macro data (RBI policy snapshot)."""

from __future__ import annotations

import logging
from functools import lru_cache

import requests

from src.utils.constants import MACRO_INDICATORS

logger = logging.getLogger(__name__)

RBI_SUMMARY_URL = "https://indiandataproject.org/data/rbi/2025-26/summary.json"
RBI_RATES_FALLBACK = "https://raw.githubusercontent.com/chirag127/oriz-rbi-rates-api/main/data/latest.json"


@lru_cache(maxsize=1)
def fetch_live_macro() -> dict:
    """Return live macro indicators; fall back to static constants on failure."""
    result = {
        "source": "mock",
        "live": False,
        "repo_rate": MACRO_INDICATORS["repo_rate"],
        "gdp_growth": MACRO_INDICATORS["gdp_growth"],
        "inflation_cpi": MACRO_INDICATORS["inflation_cpi"],
        "manufacturing_pmi": MACRO_INDICATORS["manufacturing_pmi"],
        "msme_sentiment_index": MACRO_INDICATORS["msme_sentiment_index"],
        "stance": None,
        "fetched_from": None,
    }

    try:
        resp = requests.get(RBI_SUMMARY_URL, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        result.update({
            "source": "indiandataproject.org",
            "live": True,
            "repo_rate": float(data.get("repoRate", result["repo_rate"])),
            "inflation_cpi": float(data.get("cpi", result["inflation_cpi"])),
            "stance": data.get("stance"),
            "fetched_from": RBI_SUMMARY_URL,
        })
        if data.get("forexReservesUsdBn"):
            result["forex_reserves_usd_bn"] = data["forexReservesUsdBn"]
        return result
    except Exception as exc:
        logger.warning("Live macro fetch failed (primary): %s", exc)

    try:
        resp = requests.get(RBI_RATES_FALLBACK, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        repo = (data.get("rates") or {}).get("repo")
        if repo is not None:
            result.update({
                "source": "oriz-rbi-rates-api",
                "live": True,
                "repo_rate": float(repo),
                "fetched_from": RBI_RATES_FALLBACK,
            })
    except Exception as exc:
        logger.warning("Live macro fetch failed (fallback): %s", exc)

    return result
