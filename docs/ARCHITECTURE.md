# Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit UI (app/)                          │
│  ① Select Case → ② Credit Decision → ③ Evidence → ④ Loan Offer  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Connector layer (src/connectors/)                     │
│   GST · UPI · AA · EPFO · Google · Bureau · Courts · Elec · Macro │
│   [MockConnector today] → [Real API tomorrow]                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│           Feature engineering (src/features/)                      │
│   40+ features → unified MSME feature vector                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Scoring (src/scoring/)                                │
│   Rule engine (5 pillars) + LightGBM blend → 300–900 score        │
│   Explainability · Underwriter flags · Loan simulator              │
└─────────────────────────────────────────────────────────────────┘
```

## Design principles

1. **Connector pattern** — Each data source implements `BaseConnector.fetch(profile)`. PoC reads JSON profiles; production swaps in HTTP/API clients.
2. **Explainability first** — Rule-based pillar scores drive UI; ML calibrates final score (60% rules / 40% ML by default).
3. **Underwriter workflow** — UI prioritises decision, key metrics, and charts; raw source detail is secondary (expanders).
4. **NTC focus** — Score does not require audited financials or commercial bureau file.

## Scoring pipeline

| Step | Module | Output |
|------|--------|--------|
| 1 | `extract_features()` | 40+ numeric features |
| 2 | `compute_rule_score()` | Pillar scores (0–100) + rule score |
| 3 | `predict_ml_score()` | ML-calibrated score |
| 4 | Blend | `final = 0.6 × rule + 0.4 × ML` |
| 5 | `extract_score_drivers()` | Top boosters / draggers |
| 6 | `get_risk_flags()` | Red / amber / green underwriting flags |

### Five pillars

| Pillar | Weight | Signals |
|--------|--------|---------|
| Revenue | 30% | GST turnover, filing compliance, UPI volume, electricity |
| Liquidity | 25% | ABB, EMI discipline, cashflow surplus, EPFO compliance |
| Risk | 25% | Promoter CIBIL, litigation, credit utilisation |
| Context | 10% | Sector growth, monsoon index, govt schemes |
| Reputation | 10% | Google rating, NLP sentiment, review velocity |

## ML model

- **Algorithm:** LightGBM regressor
- **Training data:** Synthetic MSME profiles with rule-derived labels + noise
- **Features:** `FEATURE_COLUMNS` in `src/features/feature_engineering.py`
- **Artifact:** `data/models/score_model.pkl`
- **Production path:** Retrain on labelled portfolio outcomes; monitor drift

## Deployment

| Environment | Method |
|-------------|--------|
| Local | `streamlit run app/main.py` |
| Cloud | Streamlit Community Cloud → `app/main.py` |
| Bootstrap | `src/bootstrap.py` seeds data + model if missing |

## Security & compliance (production notes)

- Consent framework required for AA, GST, EPFO (RBI / DPDP)
- Bureau pull needs permissible purpose and promoter consent
- Court data via licensed aggregators (e.g. eCourts feeds)
- No PII in PoC synthetic data

## Business justification

| Traditional | FinHealth Card |
|-------------|----------------|
| Requires 2–3 years audited financials | Uses digital footprint |
| Commercial bureau mandatory | Alt-data + thin-file bureau |
| Days/weeks turnaround | Minutes |
| Opaque decline | Explainable pillars + flags |
| Misses informal-sector MSMEs | GST, UPI, EPFO cover informal formalisation |
