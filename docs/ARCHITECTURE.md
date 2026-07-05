# Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit UI (app/)                          │
│  ① Portfolio → ② Stress Assessment → ③ Early Warning Signals    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Connector layer (src/connectors/)                     │
│   Loan tape · GST · UPI · AA · EPFO · Bureau · Courts · Macro   │
│   [MockConnector PoC] → [CBS / bureau API production]           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│           Feature engineering (src/features/)                      │
│   Alt-data · Collection timing · Bureau/NTC · NLP conversion    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Prediction (src/prediction/)                          │
│   Rule engine (5 pillars) + LightGBM classifier → stress prob   │
│   Structured baseline (~18%) vs full model (~90%)               │
└─────────────────────────────────────────────────────────────────┘
```

## Label logic (12-month panel)

For each `(loan_id, observation_month_t)`:

- Features at month `t` only (no leakage)
- `stress_12m = 1` if stress/default in months `t+1 … t+12`

Panel stored in `data/synthetic/panels/stress_panel.csv`.

## Scoring pipeline

| Step | Module | Output |
|------|--------|--------|
| 1 | `extract_features()` | Structured + collection + NLP vector |
| 2 | `compute_rule_stress_prob()` | Rule-based stress probability |
| 3 | `predict_ml_stress()` | ML probability (structured or full) |
| 4 | Blend | `final = 0.6 × rule + 0.4 × ML` |
| 5 | `extract_stress_drivers()` | Risk + protective factors |

### Five pillars

| Pillar | Weight | Signals |
|--------|--------|---------|
| Repayment | 30% | DPD, EMI timing, bureau other-loan on-time |
| Cashflow | 25% | GST trend, utilization, EMI burden |
| Bureau / NTC | 20% | CIBIL + other loans OR NTC alt-data proxies |
| Reputation / NLP | 15% | Text stress scores, RM escalations |
| Context | 10% | Sector, monsoon |

## Models

| Artifact | Features | Purpose |
|----------|----------|---------|
| `stress_model_structured.pkl` | Alt-data + bureau static + loan type | Baseline (~16–22%) |
| `stress_model_full.pkl` | + collections + NLP | Full model (≥90%) |

## Deployment

| Environment | Method |
|-------------|--------|
| Local | `streamlit run app/main.py` |
| Cloud | Streamlit Community Cloud → `app/main.py` |
| Bootstrap | `src/bootstrap.py` seeds data + models |
