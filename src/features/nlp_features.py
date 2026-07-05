"""Convert unstructured text into structured stress signals."""

from __future__ import annotations

import re

STRESS_KEYWORDS = {
    "insolvency": 3.0,
    "bankruptcy": 3.0,
    "default": 2.5,
    "delayed": 1.5,
    "delay": 1.5,
    "bounce": 2.0,
    "cheque": 1.2,
    "overdue": 2.0,
    "restructuring": 2.2,
    "npa": 3.0,
    "litigation": 2.0,
    "court": 1.8,
    "closure": 2.5,
    "shut": 1.5,
    "loss": 1.2,
    "decline": 1.0,
    "missed": 1.8,
    "promise": 0.8,
    "unresponsive": 1.5,
    "notice": 1.6,
    "penalty": 1.4,
    "fraud": 2.5,
    "strike": 1.2,
    "shortage": 1.0,
}

POSITIVE_KEYWORDS = {
    "timely": -1.0,
    "excellent": -1.2,
    "reliable": -1.0,
    "recommended": -0.8,
    "growth": -0.6,
    "expansion": -0.6,
    "paid": -0.5,
    "compliant": -0.8,
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def keyword_stress_density(texts: list[str]) -> float:
    """Weighted negative keyword density across text corpus (0–1 scale)."""
    if not texts:
        return 0.0
    score = 0.0
    tokens_total = 0
    for text in texts:
        tokens = _tokenize(text)
        tokens_total += max(len(tokens), 1)
        for token in tokens:
            score += STRESS_KEYWORDS.get(token, 0.0)
            score += POSITIVE_KEYWORDS.get(token, 0.0)
    density = score / tokens_total
    return max(0.0, min(1.0, density / 2.5))


def _recent_texts(items: list[dict], text_key: str = "text", days: int = 180) -> list[str]:
    return [
        item[text_key]
        for item in items
        if item.get(text_key) and item.get("days_ago", 999) <= days
    ]


def extract_nlp_features(profile: dict) -> dict:
    """Structured features derived from unstructured sources."""
    unstructured = profile.get("unstructured", {})
    google = profile.get("google", {})

    review_texts = [r.get("text", "") for r in google.get("reviews", []) if r.get("text")]
    news_texts = _recent_texts(unstructured.get("news_mentions", []), "text")
    news_headlines = _recent_texts(unstructured.get("news_mentions", []), "headline")
    rm_notes = _recent_texts(unstructured.get("rm_call_notes", []), "text")
    gst_remarks = _recent_texts(unstructured.get("gst_remarks", []), "text")
    collection_notes = _recent_texts(unstructured.get("collection_notes", []), "text")

    review_stress = keyword_stress_density(review_texts)
    news_stress = keyword_stress_density(news_texts + news_headlines)
    rm_note_stress = keyword_stress_density(rm_notes)
    gst_remark_stress = keyword_stress_density(gst_remarks)
    collection_note_stress = keyword_stress_density(collection_notes)

    negative_review_count = sum(
        1 for r in google.get("reviews", [])
        if r.get("sentiment") == "negative" and r.get("days_ago", 999) <= 180
    )
    negative_news_count = sum(
        1 for n in unstructured.get("news_mentions", [])
        if n.get("sentiment") == "negative" and n.get("days_ago", 999) <= 180
    )
    rm_escalation_count = sum(
        1 for n in unstructured.get("rm_call_notes", [])
        if n.get("sentiment") == "negative" and n.get("days_ago", 999) <= 180
    )

    composite_stress = (
        0.25 * review_stress
        + 0.25 * news_stress
        + 0.25 * rm_note_stress
        + 0.15 * gst_remark_stress
        + 0.10 * collection_note_stress
    )

    return {
        "review_stress_score": round(review_stress, 4),
        "news_stress_score": round(news_stress, 4),
        "rm_note_stress_score": round(rm_note_stress, 4),
        "gst_remark_stress_score": round(gst_remark_stress, 4),
        "collection_note_stress_score": round(collection_note_stress, 4),
        "composite_text_stress_score": round(composite_stress, 4),
        "negative_review_count_6m": negative_review_count,
        "negative_news_count_6m": negative_news_count,
        "rm_escalation_count_6m": rm_escalation_count,
        "text_signal_volume_6m": (
            negative_review_count + negative_news_count + rm_escalation_count
        ),
    }


NLP_FEATURE_COLUMNS = [
    "review_stress_score",
    "news_stress_score",
    "rm_note_stress_score",
    "gst_remark_stress_score",
    "collection_note_stress_score",
    "composite_text_stress_score",
    "negative_review_count_6m",
    "negative_news_count_6m",
    "rm_escalation_count_6m",
    "text_signal_volume_6m",
]
