"""Human-readable labels for underwriter UI."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from src.features.nlp_features import STRESS_KEYWORDS, _tokenize

SENTIMENT_SCORE = {"positive": 1, "neutral": 0, "negative": -1}
SENTIMENT_LABEL = {"positive": "Positive", "neutral": "Neutral", "negative": "Negative"}


def text_severity_label(score: float) -> str:
    if score >= 0.4:
        return "Elevated"
    if score >= 0.25:
        return "Moderate"
    if score > 0.05:
        return "Low"
    return "Minimal"


def _keyword_hits(texts: list[str], limit: int = 4) -> str:
    hits: list[str] = []
    for text in texts:
        for token in _tokenize(text):
            if token in STRESS_KEYWORDS and token not in hits:
                hits.append(token)
            if len(hits) >= limit:
                break
        if len(hits) >= limit:
            break
    return ", ".join(hits) if hits else "—"


def describe_month_on_book(profile: dict, observation_month: int | None) -> dict[str, str | int]:
    """UI copy for the loan-age snapshot used in scoring (internal: observation_month)."""
    if observation_month is None:
        return {"short": "—", "month": 0, "long": "Month on book not set."}

    obs = int(observation_month)
    lb = profile.get("loan_book", {})
    month = obs + 1
    short = f"Month {month} on book"

    lines = [
        f"Assessment uses all data recorded through **{short}**.",
        "The score estimates whether the borrower will enter **financial stress within the next 12 months**.",
    ]
    stress_onset = lb.get("stress_onset_month")
    if stress_onset is not None:
        lead = stress_onset - obs
        if lead > 0:
            lines.append(
                f"Demo timeline: stress begins at month {stress_onset + 1} on book — "
                f"**{lead} months after** this assessment point."
            )
        elif lead == 0:
            lines.append("Demo timeline: this assessment aligns with the month stress begins.")

    return {"short": short, "month": month, "long": "\n\n".join(lines)}


# Backward-compatible alias for internal callers
describe_observation_month = describe_month_on_book


def get_derived_business_metrics(features: dict, profile: dict | None = None) -> list[dict]:
    net_label = "Cashflow surplus ratio"
    net_value = f"{features.get('aa_cashflow_surplus_ratio', 0) * 100:.0f}%"
    if profile:
        aa = profile.get("aa", {})
        credits = aa.get("monthly_credits_lakhs", [])[-6:]
        debits = aa.get("monthly_debits_lakhs", [])[-6:]
        if credits and debits:
            net = sum(credits) - sum(debits)
            net_label = "Net bank inflow (6m)"
            net_value = f"₹{net:.1f}L"

    return [
        {"label": "GST filing compliance", "value": f"{features.get('gst_filing_compliance', 0) * 100:.0f}%"},
        {"label": "GST turnover YoY", "value": f"{features.get('gst_turnover_yoy_growth', 0):+.1f}%"},
        {"label": "UPI volume YoY", "value": f"{features.get('upi_volume_yoy_growth', 0):+.1f}%"},
        {"label": net_label, "value": net_value},
    ]


def get_text_intel_metrics(features: dict) -> list[dict]:
    composite = features.get("composite_text_stress_score", 0)
    return [
        {"label": "Text stress index", "value": f"{composite * 100:.0f}/100"},
        {"label": "Severity", "value": text_severity_label(composite)},
        {"label": "Negative news (6m)", "value": str(int(features.get("negative_news_count_6m", 0)))},
        {"label": "RM escalations (6m)", "value": str(int(features.get("rm_escalation_count_6m", 0)))},
    ]


def build_text_signal_table(profile: dict, features: dict) -> list[dict]:
    unstructured = profile.get("unstructured", {})
    google = profile.get("google", {})

    def _recent(items: list[dict], key: str = "text") -> list[str]:
        return [i[key] for i in items if i.get(key) and i.get("days_ago", 999) <= 180]

    sources = [
        (
            "Google reviews",
            _recent(google.get("reviews", [])),
            features.get("review_stress_score", 0),
            sum(1 for r in google.get("reviews", []) if r.get("sentiment") == "negative" and r.get("days_ago", 999) <= 180),
        ),
        (
            "News & media",
            _recent(unstructured.get("news_mentions", []), "headline")
            + _recent(unstructured.get("news_mentions", [])),
            features.get("news_stress_score", 0),
            features.get("negative_news_count_6m", 0),
        ),
        (
            "RM call notes",
            _recent(unstructured.get("rm_call_notes", [])),
            features.get("rm_note_stress_score", 0),
            features.get("rm_escalation_count_6m", 0),
        ),
        (
            "GST remarks",
            _recent(unstructured.get("gst_remarks", [])),
            features.get("gst_remark_stress_score", 0),
            len(unstructured.get("gst_remarks", [])),
        ),
        (
            "Collection notes",
            _recent(unstructured.get("collection_notes", [])),
            features.get("collection_note_stress_score", 0),
            len(unstructured.get("collection_notes", [])),
        ),
    ]

    rows = []
    for source, texts, score, count in sources:
        if not texts and score <= 0 and not count:
            continue
        rows.append(
            {
                "Source": source,
                "Signals (180d)": int(count) if count else len(texts),
                "Structured score": f"{score * 100:.0f}/100",
                "Severity": text_severity_label(score),
                "Keywords detected": _keyword_hits(texts),
            }
        )
    return rows


def collect_recent_news(profile: dict, *, limit: int = 6, max_days: int = 365) -> list[dict]:
    items = profile.get("unstructured", {}).get("news_mentions", [])
    news = []
    for item in items:
        days = int(item.get("days_ago", 999))
        if days > max_days:
            continue
        sentiment = item.get("sentiment", "neutral")
        news.append(
            {
                "days_ago": days,
                "date_label": _news_date_label(days),
                "sentiment": sentiment,
                "sentiment_label": SENTIMENT_LABEL.get(sentiment, "Neutral"),
                "headline": item.get("headline", "").strip(),
                "text": item.get("text", "").strip(),
            }
        )
    news.sort(key=lambda n: n["days_ago"])
    return news[:limit]


def build_news_sentiment_dataframe(profile: dict, *, max_days: int = 365) -> pd.DataFrame:
    rows = []
    for item in collect_recent_news(profile, limit=50, max_days=max_days):
        rows.append(
            {
                "Date": _news_date(days_ago=item["days_ago"]),
                "Days ago": item["days_ago"],
                "Sentiment score": SENTIMENT_SCORE.get(item["sentiment"], 0),
                "Sentiment": item["sentiment_label"],
                "Headline": item["headline"],
                "Summary": item["text"],
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("Date")


def _news_date(days_ago: int) -> date:
    return date.today() - timedelta(days=int(days_ago))


def _news_date_label(days_ago: int) -> str:
    return _news_date(days_ago).strftime("%d %b %Y")


def collect_text_timeline(profile: dict, limit: int = 8) -> list[dict]:
    unstructured = profile.get("unstructured", {})
    events: list[dict] = []

    for note in unstructured.get("rm_call_notes", []):
        events.append(
            {
                "days_ago": note.get("days_ago", 999),
                "source": "RM note",
                "sentiment": note.get("sentiment", "neutral"),
                "text": note.get("text", ""),
            }
        )
    for news in unstructured.get("news_mentions", []):
        events.append(
            {
                "days_ago": news.get("days_ago", 999),
                "source": "News",
                "sentiment": news.get("sentiment", "neutral"),
                "text": news.get("headline") or news.get("text", ""),
            }
        )
    for gst in unstructured.get("gst_remarks", []):
        events.append(
            {
                "days_ago": gst.get("days_ago", 999),
                "source": "GST remark",
                "sentiment": "negative",
                "text": gst.get("text", ""),
            }
        )
    for cn in unstructured.get("collection_notes", []):
        events.append(
            {
                "days_ago": cn.get("days_ago", 999),
                "source": "Collection",
                "sentiment": "negative",
                "text": cn.get("text", ""),
            }
        )
    for review in profile.get("google", {}).get("reviews", []):
        events.append(
            {
                "days_ago": review.get("days_ago", 999),
                "source": "Review",
                "sentiment": review.get("sentiment", "neutral"),
                "text": review.get("text", ""),
            }
        )

    events.sort(key=lambda e: e["days_ago"])
    return events[:limit]
