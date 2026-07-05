"""Collection and payment-timing features from loan tape + bureau other loans."""

from __future__ import annotations

from src.utils.helpers import avg_recent


def _panel_slice(panel: list[dict], months: int = 6) -> list[dict]:
    if not panel:
        return []
    return panel[-months:] if len(panel) >= months else panel


def extract_collection_features(profile: dict, observation_month: int | None = None) -> dict:
    """Payment timing and collection behaviour at observation month."""
    collections = profile.get("collections", {})
    loan_book = profile.get("loan_book", {})
    bureau = profile.get("bureau", {})

    panel = collections.get("monthly_panel", [])
    if observation_month is not None and panel:
        panel = panel[: observation_month + 1]

    recent = _panel_slice(panel, 6)
    recent_3 = _panel_slice(panel, 3)

    if not recent:
        return _empty_collection_features(loan_book, bureau)

    dpd_values = [m.get("days_past_due", 0) for m in recent]
    dpd_max = max(dpd_values) if dpd_values else 0
    dpd_avg = sum(dpd_values) / len(dpd_values)
    dpd_trend = dpd_values[-1] - dpd_values[0] if len(dpd_values) >= 2 else 0

    on_time_count = sum(1 for m in recent if m.get("days_past_due", 0) == 0)
    emi_on_time_rate_6m = on_time_count / len(recent)

    early_payment_days = [
        max(0, 5 - m.get("days_past_due", 0))
        for m in recent
        if m.get("days_past_due", 0) <= 5
    ]
    avg_payment_lead_days = sum(early_payment_days) / max(len(early_payment_days), 1)

    bounce_count_6m = sum(1 for m in recent if m.get("bounce", False))
    partial_payment_rate_6m = sum(1 for m in recent if m.get("partial_payment", False)) / len(recent)
    missed_emi_count_6m = sum(1 for m in recent if m.get("amount_paid_lakhs", 0) < m.get("amount_due_lakhs", 0) * 0.95)

    follow_up_calls_6m = sum(m.get("follow_up_calls", 0) for m in recent)
    ptp_broken_count_6m = sum(
        1 for m in recent if m.get("promise_to_pay_kept") is False
    )

    payment_delay_volatility = (
        max(dpd_values) - min(dpd_values) if len(dpd_values) >= 2 else 0
    )

    sanctioned = loan_book.get("sanctioned_amount_lakhs", 1) or 1
    outstanding = loan_book.get("outstanding_lakhs", 0)
    utilization_ratio = outstanding / sanctioned

    emi_due = loan_book.get("monthly_emi_lakhs", 0.5)
    credits = profile.get("aa", {}).get("monthly_credits_lakhs", [1])
    avg_credit = avg_recent(credits, 6)
    emi_burden_ratio = emi_due / max(avg_credit, 0.1)

    bureau_other = _bureau_other_loan_features(bureau)

    return {
        "dpd_max_6m": dpd_max,
        "dpd_avg_6m": round(dpd_avg, 2),
        "dpd_trend_6m": round(dpd_trend, 2),
        "emi_on_time_rate_6m": round(emi_on_time_rate_6m, 4),
        "avg_payment_lead_days": round(avg_payment_lead_days, 2),
        "bounce_count_6m": bounce_count_6m,
        "partial_payment_rate_6m": round(partial_payment_rate_6m, 4),
        "missed_emi_count_6m": missed_emi_count_6m,
        "follow_up_calls_6m": follow_up_calls_6m,
        "ptp_broken_count_6m": ptp_broken_count_6m,
        "payment_delay_volatility": round(payment_delay_volatility, 2),
        "utilization_ratio": round(utilization_ratio, 4),
        "emi_burden_ratio": round(emi_burden_ratio, 4),
        "months_since_disbursement": loan_book.get("months_since_disbursement", 12),
        **bureau_other,
    }


def _bureau_other_loan_features(bureau: dict) -> dict:
    """How promoter pays other loans reported in bureau."""
    other_loans = bureau.get("other_loans", [])
    if not other_loans:
        is_ntc = bureau.get("is_ntc", False)
        return {
            "bureau_other_loan_count": 0,
            "bureau_other_emi_on_time_rate": 1.0 if not is_ntc else 0.5,
            "bureau_other_avg_dpd": 0.0,
            "bureau_other_max_dpd_12m": 0,
            "bureau_other_bounce_rate": 0.0,
            "bureau_thin_file_flag": int(is_ntc),
        }

    on_time_rates = [l.get("monthly_emi_paid_on_time_rate", 1.0) for l in other_loans]
    avg_dpd_list = [l.get("avg_days_past_due", 0) for l in other_loans]
    max_dpd_list = [
        max(l.get("dpd_history_12m", [0]) or [0]) for l in other_loans
    ]
    bounce_rates = [l.get("bounce_rate_12m", 0) for l in other_loans]

    return {
        "bureau_other_loan_count": len(other_loans),
        "bureau_other_emi_on_time_rate": round(sum(on_time_rates) / len(on_time_rates), 4),
        "bureau_other_avg_dpd": round(sum(avg_dpd_list) / len(avg_dpd_list), 2),
        "bureau_other_max_dpd_12m": max(max_dpd_list),
        "bureau_other_bounce_rate": round(sum(bounce_rates) / len(bounce_rates), 4),
        "bureau_thin_file_flag": int(bureau.get("is_ntc", False)),
    }


def _empty_collection_features(loan_book: dict, bureau: dict) -> dict:
    base = {
        "dpd_max_6m": 0,
        "dpd_avg_6m": 0.0,
        "dpd_trend_6m": 0.0,
        "emi_on_time_rate_6m": 1.0,
        "avg_payment_lead_days": 3.0,
        "bounce_count_6m": 0,
        "partial_payment_rate_6m": 0.0,
        "missed_emi_count_6m": 0,
        "follow_up_calls_6m": 0,
        "ptp_broken_count_6m": 0,
        "payment_delay_volatility": 0.0,
        "utilization_ratio": 0.5,
        "emi_burden_ratio": 0.3,
        "months_since_disbursement": loan_book.get("months_since_disbursement", 12),
    }
    base.update(_bureau_other_loan_features(bureau))
    return base


COLLECTION_FEATURE_COLUMNS = [
    "dpd_max_6m",
    "dpd_avg_6m",
    "dpd_trend_6m",
    "emi_on_time_rate_6m",
    "avg_payment_lead_days",
    "bounce_count_6m",
    "partial_payment_rate_6m",
    "missed_emi_count_6m",
    "follow_up_calls_6m",
    "ptp_broken_count_6m",
    "payment_delay_volatility",
    "utilization_ratio",
    "emi_burden_ratio",
    "months_since_disbursement",
    "bureau_other_loan_count",
    "bureau_other_emi_on_time_rate",
    "bureau_other_avg_dpd",
    "bureau_other_max_dpd_12m",
    "bureau_other_bounce_rate",
    "bureau_thin_file_flag",
]
