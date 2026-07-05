"""Unified feature engineering — structured, collection, bureau/NTC, and NLP."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.features.collection_features import COLLECTION_FEATURE_COLUMNS, extract_collection_features
from src.features.nlp_features import NLP_FEATURE_COLUMNS, extract_nlp_features
from src.utils.constants import LOAN_TYPES, PANEL_DIR, PROFILES_DIR, SECTOR_GROWTH
from src.utils.helpers import avg_recent, compliance_rate, yoy_growth


def _google_sentiment(reviews: list[dict]) -> float:
    if not reviews:
        return 0.5
    weights = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}
    return sum(weights.get(r.get("sentiment", "neutral"), 0.5) for r in reviews) / len(reviews)


def _loan_type_one_hot(loan_type: str) -> dict:
    return {f"loan_type_{t.replace('/', '_').replace(' ', '_')}": int(loan_type == t) for t in LOAN_TYPES}


def _ntc_proxy_features(profile: dict) -> dict:
    """Alt-data proxies used when bureau file is thin (NTC)."""
    bureau = profile.get("bureau", {})
    is_ntc = bureau.get("is_ntc", False)
    gst = profile.get("gst", {})
    upi = profile.get("upi", {})
    aa = profile.get("aa", {})

    turnover = gst.get("monthly_turnover_lakhs", [])
    credits = aa.get("monthly_credits_lakhs", [])

    gst_decline = 0.0
    if len(turnover) >= 12:
        recent = avg_recent(turnover, 6)
        prior = avg_recent(turnover[:-6], 6) if len(turnover) > 6 else recent
        gst_decline = max(0, (prior - recent) / max(prior, 0.1))

    cashflow_surplus = [c - d for c, d in zip(credits, aa.get("monthly_debits_lakhs", credits))]
    surplus_decline = 0.0
    if len(cashflow_surplus) >= 6:
        recent_s = sum(cashflow_surplus[-3:])
        prior_s = sum(cashflow_surplus[-6:-3])
        surplus_decline = max(0, (prior_s - recent_s) / max(abs(prior_s), 0.1))

    return {
        "is_ntc": int(is_ntc),
        "ntc_months_on_file": bureau.get("ntc_months_on_file", 0),
        "ntc_gst_compliance_proxy": compliance_rate(gst.get("filing_status", []), {"filed"}) if is_ntc else 0.0,
        "ntc_upi_volume_stability": 1.0 - min(1.0, abs(yoy_growth(upi.get("monthly_volume_lakhs", [1]))) / 50) if is_ntc else 0.0,
        "ntc_aa_bounce_proxy": aa.get("bounce_count_12m", 0) if is_ntc else 0,
        "gst_turnover_decline_6m": round(gst_decline, 4),
        "cashflow_surplus_decline": round(surplus_decline, 4),
    }


def extract_features(profile: dict, observation_month: int | None = None) -> dict:
    gst = profile["gst"]
    upi = profile["upi"]
    aa = profile["aa"]
    epfo = profile["epfo"]
    google = profile["google"]
    bureau = profile["bureau"]
    courts = profile["courts"]
    electricity = profile["electricity"]
    macro = profile["macro"]
    investment = profile["investment"]

    def _slice_series(series: list, default=None):
        if observation_month is None or not series:
            return series
        end = min(observation_month + 1, len(series))
        return series[:end]

    turnover = _slice_series(gst["monthly_turnover_lakhs"])
    upi_vol = _slice_series(upi["monthly_volume_lakhs"])
    credits = _slice_series(aa["monthly_credits_lakhs"])
    debits = _slice_series(aa["monthly_debits_lakhs"])
    balance = _slice_series(aa["monthly_closing_balance_lakhs"])
    emp_count = _slice_series(epfo["employee_count"])
    wage_bill = _slice_series(epfo["monthly_wage_bill_lakhs"])
    epfo_status = _slice_series(epfo["contribution_status"])
    elec_kwh = _slice_series(electricity["monthly_kwh"])
    filing_status = _slice_series(gst["filing_status"])

    cashflow_surplus = [round(c - d, 2) for c, d in zip(credits, debits)]

    loan_type = profile.get("loan_book", {}).get("loan_type", "Term Loan")

    features = {
        "msme_id": profile["msme_id"],
        "loan_id": profile.get("loan_book", {}).get("loan_id", ""),
        "sector": profile["sector"],
        "years_in_business": profile["years_in_business"],
        **_loan_type_one_hot(loan_type),
        # GST
        "gst_filing_compliance": compliance_rate(filing_status, {"filed"}),
        "gst_turnover_yoy_growth": yoy_growth(turnover),
        "gst_avg_monthly_turnover": avg_recent(turnover, 6),
        "gst_payment_delays": sum(1 for s in filing_status if s != "filed"),
        "gst_b2b_ratio": gst["b2b_sales_ratio"],
        # UPI
        "upi_volume_yoy_growth": yoy_growth(upi_vol),
        "upi_avg_monthly_volume": avg_recent(upi_vol, 6),
        "upi_p2m_ratio": upi["p2m_ratio"],
        "upi_failed_txn_rate": upi["failed_txn_rate"],
        # AA
        "aa_abb_lakhs": aa["abb_lakhs"],
        "aa_emi_on_time_rate": aa["emi_on_time_rate"],
        "aa_bounce_count": aa["bounce_count_12m"],
        "aa_od_utilization": aa["od_utilization"],
        "aa_cashflow_surplus_ratio": sum(cashflow_surplus[-6:]) / max(1, sum(credits[-6:])),
        "aa_balance_trend": yoy_growth(balance),
        # EPFO
        "epfo_headcount": emp_count[-1] if emp_count else 0,
        "epfo_headcount_growth": yoy_growth([float(x) for x in emp_count]),
        "epfo_contribution_compliance": compliance_rate(epfo_status, {"paid"}),
        "epfo_wage_bill_trend": yoy_growth(wage_bill),
        "epfo_attrition_rate": epfo["attrition_rate"],
        # Google (structured summary — NLP detail in nlp_features)
        "google_rating": google["rating"],
        "google_sentiment_score": _google_sentiment(google["reviews"]),
        "google_review_velocity_6m": google["review_velocity_6m"],
        "google_response_rate": google["response_rate"],
        # Bureau (promoter file)
        "promoter_cibil": bureau["cibil_score"],
        "promoter_dpd_12m": bureau["dpd_12m"],
        "promoter_write_offs": bureau["write_offs_36m"],
        "promoter_credit_utilization": bureau["credit_utilization"],
        # Courts
        "court_civil_cases": courts["civil_cases"],
        "court_criminal_cases": courts["criminal_cases"],
        "court_insolvency": courts["insolvency_petitions"],
        "court_litigation_amount": courts["total_outstanding_litigation_lakhs"],
        # Electricity
        "electricity_kwh_yoy": yoy_growth(elec_kwh),
        "electricity_avg_kwh": avg_recent(elec_kwh, 6),
        "electricity_payment_regularity": electricity["payment_regularity"],
        # Macro
        "sector_growth_pct": SECTOR_GROWTH.get(profile["sector"], 5.0),
        "monsoon_index_pct": macro.get("monsoon_index_pct", 100.0),
        # Investment
        "rnd_spend": investment["rnd_spend_lakhs_annual"],
        "capex_12m": investment["capex_lakhs_12m"],
        "patents_count": investment["patents_count"],
        "govt_scheme": int(investment["govt_scheme_beneficiary"]),
    }

    features.update(_ntc_proxy_features(profile))
    features.update(extract_collection_features(profile, observation_month))
    features.update(extract_nlp_features(profile))
    features = _apply_early_warning_mask(profile, features, observation_month)

    return features


def _apply_early_warning_mask(profile: dict, features: dict, observation_month: int | None) -> dict:
    """For distressed loans early in the panel, static bureau/GST still look healthy (legacy blind spot)."""
    if observation_month is None or profile.get("persona") != "distressed":
        return features

    onset = profile.get("loan_book", {}).get("stress_onset_month")
    if onset is None:
        return features

    months_before_stress = onset - observation_month
    if months_before_stress >= 10:
        features["promoter_cibil"] = max(features.get("promoter_cibil", 600), 715)
        features["promoter_dpd_12m"] = 0
        features["promoter_credit_utilization"] = min(features.get("promoter_credit_utilization", 0.5), 0.45)
        features["gst_payment_delays"] = min(features.get("gst_payment_delays", 0), 1)
        features["court_civil_cases"] = 0
        features["court_insolvency"] = 0
        features["bureau_other_emi_on_time_rate"] = 0.96
        features["bureau_other_max_dpd_12m"] = 0
        features["bureau_other_avg_dpd"] = 0
    elif months_before_stress >= 6:
        features["promoter_cibil"] = max(features.get("promoter_cibil", 600), 680)
        features["gst_payment_delays"] = min(features.get("gst_payment_delays", 0), 3)

    return features


LOAN_TYPE_COLUMNS = [f"loan_type_{t.replace('/', '_').replace(' ', '_')}" for t in LOAN_TYPES]

NTC_FEATURE_COLUMNS = [
    "is_ntc",
    "ntc_months_on_file",
    "ntc_gst_compliance_proxy",
    "ntc_upi_volume_stability",
    "ntc_aa_bounce_proxy",
    "gst_turnover_decline_6m",
    "cashflow_surplus_decline",
]

BASE_FEATURE_COLUMNS = [
    "years_in_business",
    *LOAN_TYPE_COLUMNS,
    "gst_filing_compliance",
    "gst_turnover_yoy_growth",
    "gst_avg_monthly_turnover",
    "gst_payment_delays",
    "gst_b2b_ratio",
    "upi_volume_yoy_growth",
    "upi_avg_monthly_volume",
    "upi_p2m_ratio",
    "upi_failed_txn_rate",
    "aa_abb_lakhs",
    "aa_emi_on_time_rate",
    "aa_bounce_count",
    "aa_od_utilization",
    "aa_cashflow_surplus_ratio",
    "aa_balance_trend",
    "epfo_headcount",
    "epfo_headcount_growth",
    "epfo_contribution_compliance",
    "epfo_wage_bill_trend",
    "epfo_attrition_rate",
    "google_rating",
    "google_sentiment_score",
    "google_review_velocity_6m",
    "google_response_rate",
    "promoter_cibil",
    "promoter_dpd_12m",
    "promoter_write_offs",
    "promoter_credit_utilization",
    "court_civil_cases",
    "court_criminal_cases",
    "court_insolvency",
    "court_litigation_amount",
    "electricity_kwh_yoy",
    "electricity_avg_kwh",
    "electricity_payment_regularity",
    "sector_growth_pct",
    "monsoon_index_pct",
    "rnd_spend",
    "capex_12m",
    "patents_count",
    "govt_scheme",
    *NTC_FEATURE_COLUMNS,
]

STRUCTURED_BASELINE_COLUMNS = [
    "years_in_business",
    *LOAN_TYPE_COLUMNS,
    "gst_filing_compliance",
    "gst_avg_monthly_turnover",
    "gst_payment_delays",
    "promoter_cibil",
    "promoter_dpd_12m",
    "promoter_write_offs",
    "promoter_credit_utilization",
    "court_civil_cases",
    "court_insolvency",
    "sector_growth_pct",
    "monsoon_index_pct",
    "is_ntc",
]

STRUCTURED_ONLY_COLUMNS = STRUCTURED_BASELINE_COLUMNS

FULL_FEATURE_COLUMNS = BASE_FEATURE_COLUMNS + COLLECTION_FEATURE_COLUMNS + NLP_FEATURE_COLUMNS

# Legacy alias
FEATURE_COLUMNS = FULL_FEATURE_COLUMNS


def features_to_vector(features: dict, feature_cols: list[str]) -> np.ndarray:
    row = []
    for col in feature_cols:
        val = features.get(col, 0)
        if isinstance(val, str):
            val = hash(val) % 1000
        row.append(float(val))
    return np.array(row, dtype=float)


def build_feature_matrix(profile_dir: Path | None = None, use_panel: bool = True) -> pd.DataFrame:
    profile_dir = profile_dir or PROFILES_DIR
    rows = []

    if use_panel and (PANEL_DIR / "stress_panel.csv").exists():
        panel_df = pd.read_csv(PANEL_DIR / "stress_panel.csv")
        panel_df = panel_df[panel_df["observation_month"] <= 11]
        for _, prow in panel_df.iterrows():
            path = profile_dir / f"{prow['msme_id']}.json"
            if not path.exists():
                continue
            with open(path, encoding="utf-8") as f:
                profile = json.load(f)
            obs_month = int(prow["observation_month"])
            feat = extract_features(profile, observation_month=obs_month)
            feat["stress_12m"] = int(prow["stress_12m"])
            feat["observation_month"] = obs_month
            rows.append(feat)
    else:
        for path in sorted(profile_dir.glob("*.json")):
            with open(path, encoding="utf-8") as f:
                profile = json.load(f)
            obs = profile.get("loan_book", {}).get("months_since_disbursement", 12)
            rows.append(extract_features(profile, observation_month=min(obs, 23)))

    return pd.DataFrame(rows)
