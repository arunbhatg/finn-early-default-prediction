"""Generate synthetic MSME profiles with loan tape, collections, bureau, and unstructured data."""

from __future__ import annotations

import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from faker import Faker

from src.utils.constants import (
    DEMO_LOAN_TYPE_MAP,
    DEMO_PERSONAS,
    LOAN_TYPES,
    PANEL_DIR,
    PROFILES_DIR,
    SYNTHETIC_DIR,
)
from src.utils.helpers import generate_gstin, generate_pan

fake = Faker("en_IN")
SECTORS = list(
    {
        "Manufacturing",
        "Retail",
        "Services",
        "Agri-Input",
        "Textiles",
        "Pharma",
        "Food Processing",
        "Logistics",
    }
)
STATES = {
    "Maharashtra": "27",
    "Gujarat": "24",
    "Karnataka": "29",
    "Delhi": "07",
    "Tamil Nadu": "33",
    "Rajasthan": "08",
}

PERSONA_LOAN_TYPE = {
    "healthy_manufacturer": "Term Loan",
    "healthy_retail": "Cash Credit",
    "distressed": "Working Capital",
    "agri_favorable": "Mudra/PMEGP",
}


def _trend(base: float, months: int, growth: float, noise: float, rng: random.Random) -> list[float]:
    values = []
    current = base
    for _ in range(months):
        drift = 1 + (growth / 100 / 12)
        current = max(0, current * drift + rng.uniform(-noise, noise))
        values.append(round(current, 2))
    return values


def _status_series(
    months: int,
    compliance: float,
    rng: random.Random,
    good: str = "filed",
    bad: tuple[str, ...] = ("delayed", "missed"),
) -> list[str]:
    return [good if rng.random() < compliance else rng.choice(bad) for _ in range(months)]


def _review_text(sentiment: str, rng: random.Random) -> str:
    pools = {
        "positive": [
            "Excellent quality products and timely delivery.",
            "Very professional team, highly recommended.",
            "Reliable supplier — payments always honoured.",
        ],
        "negative": [
            "Delayed delivery and poor communication.",
            "Payment issues and unresponsive staff — cheque bounce reported.",
            "Business seems to be declining, missed deadlines.",
        ],
        "neutral": ["Average experience, nothing exceptional.", "Decent products at market rates."],
    }
    return rng.choice(pools[sentiment])


def _build_collections_panel(
    persona: str,
    emi_lakhs: float,
    months: int,
    rng: random.Random,
) -> tuple[list[dict], int | None]:
    """Build monthly collection panel; return (panel, stress_onset_month_index)."""
    panel = []
    stress_onset = None

    if persona == "distressed":
        stress_onset = months - 10
        early_dpd = 0
        mid_dpd = rng.randint(5, 15)
        late_dpd = rng.randint(35, 60)
    elif persona == "healthy_retail":
        early_dpd, mid_dpd, late_dpd = 0, rng.randint(0, 3), rng.randint(0, 5)
    else:
        early_dpd, mid_dpd, late_dpd = 0, 0, rng.randint(0, 2)

    base_date = date.today() - timedelta(days=months * 30)

    for i in range(months):
        if persona == "distressed":
            if i < stress_onset - 12:
                dpd = early_dpd
            elif i < stress_onset:
                dpd = mid_dpd + rng.randint(0, 5)
            else:
                dpd = late_dpd + rng.randint(0, 10)
        else:
            dpd = early_dpd if i < months - 6 else mid_dpd

        due = base_date + timedelta(days=i * 30)
        paid = due + timedelta(days=dpd)
        bounce = dpd > 10 and rng.random() < 0.4
        partial = dpd > 5 and rng.random() < 0.3
        paid_amt = emi_lakhs * (0.6 if partial else 1.0)

        panel.append(
            {
                "month_index": i,
                "emi_due_date": due.isoformat(),
                "emi_paid_date": paid.isoformat(),
                "days_past_due": dpd,
                "amount_due_lakhs": round(emi_lakhs, 2),
                "amount_paid_lakhs": round(paid_amt, 2),
                "partial_payment": partial,
                "bounce": bounce,
                "follow_up_calls": rng.randint(0, 3) if dpd > 5 else 0,
                "promise_to_pay_kept": dpd <= 5 or rng.random() > 0.4,
            }
        )

    return panel, stress_onset


def _build_bureau_other_loans(persona: str, is_ntc: bool, rng: random.Random) -> list[dict]:
    if is_ntc:
        return []

    loans = []
    n = 0 if persona == "distressed" else rng.randint(1, 2)
    for _ in range(n):
        if persona == "distressed":
            dpd_hist = [0] * 6 + [rng.randint(15, 45) if rng.random() > 0.5 else 0 for _ in range(6)]
            on_time = round(rng.uniform(0.55, 0.75), 2)
            avg_dpd = round(rng.uniform(8, 25), 1)
            bounce = round(rng.uniform(0.1, 0.35), 2)
        else:
            dpd_hist = [0] * 12
            on_time = round(rng.uniform(0.92, 1.0), 2)
            avg_dpd = 0.0
            bounce = round(rng.uniform(0, 0.05), 2)

        loans.append(
            {
                "lender": rng.choice(["HDFC", "ICICI", "SBI", "Axis", "Bajaj Finance"]),
                "product": rng.choice(["Home Loan", "Auto Loan", "Personal Loan", "Business Loan"]),
                "sanctioned_lakhs": round(rng.uniform(5, 80), 2),
                "monthly_emi_paid_on_time_rate": on_time,
                "dpd_history_12m": dpd_hist,
                "avg_days_past_due": avg_dpd,
                "bounce_rate_12m": bounce,
            }
        )
    return loans


def _build_unstructured(persona: str, business_name: str, rng: random.Random) -> dict:
    if persona == "distressed":
        news = [
            {"headline": f"{business_name} faces supplier payment delays", "text": "Local traders report overdue payments and cheque bounce issues.", "sentiment": "negative", "days_ago": rng.randint(30, 120)},
            {"headline": "GST notice issued for delayed filing", "text": "Tax department issued notice for consecutive delayed GST returns.", "sentiment": "negative", "days_ago": rng.randint(45, 90)},
        ]
        rm_notes = [
            {"text": "Promoter requested restructuring — cashflow tight, missed last EMI by 12 days.", "sentiment": "negative", "days_ago": rng.randint(15, 60)},
            {"text": "Promise to pay broken — customer said payment by 15th but bounced.", "sentiment": "negative", "days_ago": rng.randint(10, 40)},
        ]
        gst_remarks = [
            {"text": "Show cause notice for delayed GST payment — penalty applicable.", "days_ago": rng.randint(60, 150), "type": "notice"},
        ]
        collection_notes = [
            {"text": "Field visit — partial payment received, balance overdue 35 days.", "days_ago": rng.randint(5, 30)},
        ]
    elif persona in {"healthy_manufacturer", "healthy_retail", "agri_favorable"}:
        news = [{"headline": f"{business_name} expands operations", "text": "Business reports steady growth and timely vendor payments.", "sentiment": "positive", "days_ago": rng.randint(30, 180)}]
        rm_notes = [{"text": "Routine review — promoter maintains healthy payment discipline on all facilities.", "sentiment": "positive", "days_ago": rng.randint(30, 90)}]
        gst_remarks = []
        collection_notes = []
    else:
        news = []
        rm_notes = [{"text": "Standard monitoring call — no concerns.", "sentiment": "neutral", "days_ago": rng.randint(30, 90)}]
        gst_remarks = []
        collection_notes = []

    return {
        "news_mentions": news,
        "rm_call_notes": rm_notes,
        "gst_remarks": gst_remarks,
        "collection_notes": collection_notes,
    }


def _compute_stress_labels(panel: list[dict], stress_onset: int | None, horizon: int = 12) -> list[dict]:
    """For each observation month t, label=1 if stress within next `horizon` months (inclusive)."""
    labels = []
    n = len(panel)
    for t in range(n):
        future_start = t + 1
        future_end = min(t + horizon, n - 1)  # inclusive end index
        stressed = False
        if stress_onset is not None and future_start <= stress_onset <= future_end:
            stressed = True
        if not stressed and future_end >= future_start:
            for m in panel[future_start : future_end + 1]:
                if m.get("days_past_due", 0) >= 30:
                    stressed = True
                    break
        labels.append({"observation_month": t, "stress_12m": int(stressed)})
    return labels


def build_profile(
    msme_id: str,
    persona: str,
    sector: str,
    state: str,
    city: str,
    business_name: str,
    rng: random.Random,
    loan_type: str | None = None,
    force_ntc: bool | None = None,
) -> dict:
    state_code = STATES.get(state, "27")
    gstin = generate_gstin(state_code, rng)
    pan = generate_pan(rng)
    loan_type = loan_type or PERSONA_LOAN_TYPE.get(persona, rng.choice(LOAN_TYPES))

    if persona == "healthy_manufacturer":
        turnover_growth, compliance, emp_stability = 15, 0.98, 0.95
        bureau_score, court_cases = rng.randint(760, 820), 0
        review_sentiment, electricity_growth = "positive", 12
        monsoon_index = rng.uniform(98, 110)
        is_ntc = False
    elif persona == "healthy_retail":
        turnover_growth, compliance, emp_stability = 18, 0.96, 0.92
        bureau_score, court_cases = 0, 0  # NTC — no bureau score
        review_sentiment, electricity_growth = "positive", 5
        monsoon_index = rng.uniform(95, 105)
        is_ntc = True
    elif persona == "distressed":
        turnover_growth, compliance, emp_stability = -8, 0.55, 0.6
        bureau_score, court_cases = rng.randint(580, 660), rng.randint(1, 3)
        review_sentiment, electricity_growth = "negative", -15
        monsoon_index = rng.uniform(85, 95)
        is_ntc = False
    elif persona == "agri_favorable":
        turnover_growth, compliance, emp_stability = 10, 0.94, 0.9
        bureau_score, court_cases = 0, 0
        review_sentiment, electricity_growth = "positive", 6
        monsoon_index = rng.uniform(108, 118)
        is_ntc = True
    else:
        turnover_growth = rng.uniform(-5, 20)
        compliance = rng.uniform(0.65, 0.99)
        emp_stability = rng.uniform(0.7, 0.98)
        is_ntc = rng.random() < 0.35
        bureau_score = 0 if is_ntc else int(rng.uniform(600, 820))
        court_cases = rng.choices([0, 0, 0, 1, 2], weights=[5, 5, 5, 3, 1])[0]
        review_sentiment = rng.choices(["positive", "neutral", "negative"], weights=[6, 3, 1])[0]
        electricity_growth = rng.uniform(-10, 15)
        monsoon_index = rng.uniform(85, 115)

    if force_ntc is not None:
        is_ntc = force_ntc
        if is_ntc:
            bureau_score = 0

    monthly_turnover = _trend(rng.uniform(8, 40), 24, turnover_growth, 1.5, rng)
    monthly_filings = _status_series(24, compliance, rng)
    monthly_upi_volume = _trend(rng.uniform(2, 25), 12, turnover_growth * 1.2, 0.8, rng)
    monthly_balance = _trend(rng.uniform(1, 15), 12, turnover_growth * 0.5, 0.5, rng)
    monthly_credits = _trend(rng.uniform(5, 30), 12, turnover_growth, 1.2, rng)
    monthly_debits = [round(c * rng.uniform(0.75, 0.95), 2) for c in monthly_credits]
    employee_count = [max(1, int(x)) for x in _trend(rng.randint(5, 40), 12, turnover_growth * 0.3, 0.5, rng)]
    wage_bill = [round(c * rng.uniform(18000, 28000), 2) for c in employee_count]
    epfo_status = _status_series(12, emp_stability, rng, good="paid", bad=("delayed", "missed"))
    electricity_kwh = _trend(rng.uniform(500, 5000), 12, electricity_growth, 100, rng)

    num_reviews = rng.randint(12, 45)
    sentiment_weights = {"positive": [0.75, 0.2, 0.05], "neutral": [0.4, 0.45, 0.15], "negative": [0.15, 0.25, 0.6]}[review_sentiment]
    reviews = []
    for _ in range(num_reviews):
        s = rng.choices(["positive", "neutral", "negative"], weights=sentiment_weights)[0]
        reviews.append(
            {
                "rating": rng.choices([5, 4, 3, 2, 1], weights=[5, 3, 2, 1, 1] if s == "positive" else [1, 1, 2, 3, 5])[0],
                "text": _review_text(s, rng),
                "sentiment": s,
                "days_ago": rng.randint(1, 540),
            }
        )

    sanctioned = round(rng.uniform(10, 150), 2)
    emi_lakhs = round(sanctioned * rng.uniform(0.015, 0.025), 2)
    months_since = rng.randint(6, 36)
    collection_panel, stress_onset = _build_collections_panel(persona, emi_lakhs, 24, rng)
    observation_labels = _compute_stress_labels(collection_panel, stress_onset)
    outstanding = round(sanctioned * rng.uniform(0.4, 0.95 if persona == "distressed" else 0.7), 2)

    profile = {
        "msme_id": msme_id,
        "business_name": business_name,
        "pan": pan,
        "gstin": gstin,
        "sector": sector,
        "city": city,
        "state": state,
        "years_in_business": rng.randint(2, 18),
        "udyam_number": f"UDYAM-{state_code[:2]}-{rng.randint(1000000, 9999999)}",
        "persona": persona,
        "loan_book": {
            "loan_id": f"LN-{msme_id}-001",
            "loan_type": loan_type,
            "sanctioned_amount_lakhs": sanctioned,
            "outstanding_lakhs": outstanding,
            "interest_rate_pct": round(rng.uniform(9.5, 14.5), 2),
            "tenure_months": rng.choice([24, 36, 48, 60]),
            "monthly_emi_lakhs": emi_lakhs,
            "collateral_type": rng.choice(["None", "Property", "Stock", "Equipment", "CGTMSE"]),
            "disbursement_date": (date.today() - timedelta(days=months_since * 30)).isoformat(),
            "months_since_disbursement": months_since,
            "stress_onset_month": stress_onset,
        },
        "collections": {"monthly_panel": collection_panel},
        "observation_labels": observation_labels,
        "unstructured": _build_unstructured(persona, business_name, rng),
        "gst": {
            "registration_date": fake.date_between(start_date="-10y", end_date="-1y").isoformat(),
            "business_type": sector,
            "monthly_turnover_lakhs": monthly_turnover,
            "filing_status": monthly_filings,
            "b2b_sales_ratio": round(rng.uniform(0.3, 0.9), 2),
            "payment_delays_count": sum(1 for s in monthly_filings if s != "filed"),
            "primary_customer_sectors": dict(zip(rng.sample(SECTORS, k=3), np.random.dirichlet(np.ones(3)).round(2).tolist())),
        },
        "upi": {
            "vpa": f"{business_name.split()[0].lower()}@{rng.choice(['okaxis', 'paytm', 'ybl'])}",
            "monthly_txn_count": [int(v / rng.uniform(200, 800)) for v in monthly_upi_volume],
            "monthly_volume_lakhs": monthly_upi_volume,
            "avg_ticket_size": [round(v / max(1, int(v / 500)), 2) for v in monthly_upi_volume],
            "p2m_ratio": round(rng.uniform(0.55, 0.95), 2),
            "failed_txn_rate": round(rng.uniform(0.005, 0.05 if persona == "distressed" else 0.02), 3),
        },
        "aa": {
            "consent_id": f"AA-CONSENT-{msme_id}",
            "accounts": [{"bank": rng.choice(["HDFC", "ICICI", "SBI", "Axis"]), "type": "current"}],
            "monthly_closing_balance_lakhs": monthly_balance,
            "monthly_credits_lakhs": monthly_credits,
            "monthly_debits_lakhs": monthly_debits,
            "abb_lakhs": round(sum(monthly_balance[-3:]) / 3, 2),
            "emi_on_time_rate": round(rng.uniform(0.7, 0.99 if persona != "distressed" else 0.75), 2),
            "bounce_count_12m": 0 if persona != "distressed" else rng.randint(1, 4),
            "od_utilization": round(rng.uniform(0.1, 0.75 if persona == "distressed" else 0.4), 2),
        },
        "epfo": {
            "establishment_id": f"{state[:2].upper()}/{city[:3].upper()}/{rng.randint(100000, 999999)}",
            "employee_count": employee_count,
            "monthly_wage_bill_lakhs": wage_bill,
            "contribution_status": epfo_status,
            "new_joiners_12m": rng.randint(0, 8),
            "attrition_rate": round(rng.uniform(0.05, 0.25 if persona == "distressed" else 0.12), 2),
        },
        "google": {
            "place_id": f"ChIJ{msme_id}",
            "rating": round(rng.uniform(3.2, 4.8 if review_sentiment == "positive" else 3.8), 1),
            "review_count": num_reviews,
            "reviews": reviews,
            "response_rate": round(rng.uniform(0.4, 0.95), 2),
            "review_velocity_6m": sum(1 for r in reviews if r["days_ago"] <= 180),
        },
        "bureau": {
            "promoter_name": fake.name(),
            "cibil_score": bureau_score,
            "is_ntc": is_ntc,
            "ntc_months_on_file": 0 if is_ntc else rng.randint(24, 120),
            "active_loans": len(_build_bureau_other_loans(persona, is_ntc, rng)),
            "other_loans": _build_bureau_other_loans(persona, is_ntc, rng),
            "dpd_12m": 0 if bureau_score > 700 or is_ntc else rng.randint(1, 3),
            "write_offs_36m": 1 if bureau_score < 650 and not is_ntc else 0,
            "credit_utilization": round(rng.uniform(0.2, 0.85 if persona == "distressed" else 0.45), 2),
        },
        "courts": {
            "civil_cases": court_cases if court_cases else 0,
            "criminal_cases": 1 if persona == "distressed" and rng.random() > 0.5 else 0,
            "insolvency_petitions": 1 if persona == "distressed" and court_cases >= 2 else 0,
            "total_outstanding_litigation_lakhs": round(court_cases * rng.uniform(2, 15), 2),
        },
        "electricity": {
            "consumer_number": f"ELC{rng.randint(100000, 999999)}",
            "monthly_kwh": electricity_kwh,
            "tariff_category": "Industrial" if sector == "Manufacturing" else "Commercial",
            "payment_regularity": round(compliance, 2),
        },
        "macro": {
            "sector_growth_pct": None,
            "monsoon_index_pct": round(monsoon_index, 1),
            "region_tier": rng.choice(["Metro", "Tier-1", "Tier-2"]),
        },
        "investment": {
            "rnd_spend_lakhs_annual": round(rng.uniform(0, 5 if persona == "healthy_manufacturer" else 1.5), 2),
            "capex_lakhs_12m": round(rng.uniform(0, 20 if persona == "healthy_manufacturer" else 5), 2),
            "patents_count": rng.randint(0, 3 if persona == "healthy_manufacturer" else 1),
            "govt_scheme_beneficiary": persona in {"healthy_manufacturer", "agri_favorable"},
        },
    }
    return profile


def _loan_type_for_index(i: int, rng: random.Random) -> str:
    return LOAN_TYPES[i % len(LOAN_TYPES)]


def generate_all(seed: int = 42, count: int = 75) -> None:
    rng = random.Random(seed)
    np.random.seed(seed)

    PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

    master_rows = []
    panel_rows = []
    persona_map = {
        "MSME001": ("healthy_manufacturer", "Manufacturing", "Maharashtra", "Pune"),
        "MSME002": ("healthy_retail", "Retail", "Gujarat", "Ahmedabad"),
        "MSME003": ("distressed", "Retail", "Delhi", "Delhi"),
        "MSME004": ("agri_favorable", "Agri-Input", "Maharashtra", "Nagpur"),
    }

    for i in range(count):
        msme_id = f"MSME{i+1:03d}"
        if msme_id in persona_map:
            persona, sector, state, city = persona_map[msme_id]
            business_name = DEMO_PERSONAS[msme_id]["name"]
            loan_type = DEMO_LOAN_TYPE_MAP.get(msme_id)
            force_ntc = DEMO_PERSONAS[msme_id].get("is_ntc")
        else:
            persona = rng.choices(
                ["random", "distressed", "healthy_manufacturer", "healthy_retail"],
                weights=[40, 25, 20, 15],
            )[0]
            sector = rng.choice(list(SECTORS))
            state = rng.choice(list(STATES.keys()))
            city = fake.city()
            business_name = fake.company()
            loan_type = _loan_type_for_index(i, rng)
            force_ntc = None

        profile = build_profile(
            msme_id, persona, sector, state, city, business_name, rng,
            loan_type=loan_type, force_ntc=force_ntc,
        )
        path = PROFILES_DIR / f"{msme_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)

        lb = profile["loan_book"]
        master_rows.append(
            {
                "msme_id": msme_id,
                "loan_id": lb["loan_id"],
                "business_name": business_name,
                "loan_type": lb["loan_type"],
                "sanctioned_lakhs": lb["sanctioned_amount_lakhs"],
                "outstanding_lakhs": lb["outstanding_lakhs"],
                "is_ntc": profile["bureau"]["is_ntc"],
                "sector": sector,
                "city": city,
                "state": state,
                "persona": persona,
            }
        )

        for obs in profile.get("observation_labels", []):
            panel_rows.append(
                {
                    "msme_id": msme_id,
                    "loan_id": lb["loan_id"],
                    "observation_month": obs["observation_month"],
                    "stress_12m": obs["stress_12m"],
                }
            )

    pd.DataFrame(master_rows).to_csv(SYNTHETIC_DIR / "loan_portfolio.csv", index=False)
    pd.DataFrame(master_rows).to_csv(SYNTHETIC_DIR / "msme_master.csv", index=False)
    pd.DataFrame(panel_rows).to_csv(PANEL_DIR / "stress_panel.csv", index=False)
    print(f"Generated {count} profiles in {PROFILES_DIR}")
    print(f"Panel rows: {len(panel_rows)} in {PANEL_DIR / 'stress_panel.csv'}")


if __name__ == "__main__":
    generate_all()
