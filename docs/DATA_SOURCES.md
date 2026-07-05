# Data Sources — Real vs Dummy & Replacement Guide

## Summary table

| Source | PoC (today) | Partially real possible | Production integration |
|--------|-------------|-------------------------|------------------------|
| **GST** | Synthetic GSTR JSON | Sector benchmarks from public reports | GST Suvidha Provider / GSP APIs, OCR on returns |
| **UPI** | Synthetic merchant volumes | — | NPCI / bank merchant APIs (licensed) |
| **Account Aggregator** | Synthetic bank series | — | RBI AA framework (FIU + FIP consent flow) |
| **EPFO** | Synthetic establishment data | — | EPFO employer API (authorised access) |
| **Google Business** | Synthetic reviews + NLP | Places API for public reviews | Google Places API + sentiment model |
| **Promoter bureau** | Synthetic CIBIL-like score | — | CIBIL / CRIF / Experian commercial API |
| **Courts** | Synthetic docket counts | — | eCourts / legal data aggregators |
| **Electricity** | Synthetic kWh series | — | Discom APIs or bill OCR |
| **Macro / sector** | Static JSON (RBI-style) | **Yes** — RBI, MOSPI public data | Scheduled ETL from official releases |
| **Investment / R&D** | Synthetic flags | MCA filings (public) | MCA21 API for charges, patents |

## What is real in the PoC

- **Scoring logic** — Production-shaped rule engine + trained ML
- **Feature engineering** — Real formulas (YoY growth, compliance rates, ABB)
- **Sector growth table** — Representative of published sector trends (static)
- **Macro constants** — Repo rate, PMI placeholders in `src/utils/constants.py`
- **NLP sentiment** — Real VADER-style logic on review text (synthetic text)

## What is dummy

- All **borrower-level** records under `data/synthetic/profiles/`
- **Connector fetch** — Reads local JSON, simulates API latency in UI only
- **Consent flow** — UI checkbox simulation, no actual AA consent artefact
- **Loan approval** — Policy simulation, not core banking integration

## Connector replacement pattern

Each connector lives in `src/connectors/sources.py` and implements:

```python
class GSTConnector(BaseConnector):
    source_name = "gst"

    def fetch(self, profile: dict) -> dict:
        return profile["gst"]  # PoC: from JSON
```

### Step-by-step to go live

1. **Create** `src/connectors/live/gst_live.py` with `fetch_live(gstin: str) -> dict` calling real API.
2. **Map** API response to the same schema as synthetic `profile["gst"]`.
3. **Switch** connector via config:

```python
# src/utils/constants.py
USE_LIVE_CONNECTORS = os.getenv("USE_LIVE_CONNECTORS", "false") == "true"
```

4. **Run feature pipeline unchanged** — `extract_features()` expects the same keys.
5. **Add tests** with recorded API fixtures.

### Schema contract (GST example)

```json
{
  "monthly_turnover_lakhs": [12.5, 13.1, ...],
  "filing_status": ["filed", "filed", "delayed", ...],
  "b2b_sales_ratio": 0.72,
  "payment_delays_count": 0
}
```

If live API returns different field names, map in the connector — **never** in feature engineering.

## Per-source integration notes

### GST
- **Provider:** GSP (e.g. Clear, IRIS) or direct GSTN (licensed)
- **Data:** GSTR-1, GSTR-3B, turnover, filing dates
- **Consent:** GSTIN + OTP / digital consent

### Account Aggregator
- **Framework:** RBI AA (FIU registers with Sahamati)
- **Flow:** Consent artefact → FIP fetch → normalised FI data
- **Maps to:** `aa.monthly_credits_lakhs`, `abb_lakhs`, `emi_on_time_rate`

### EPFO
- **Data:** Establishment ID, contribution history, employee count
- **Use:** Validates payroll vs declared turnover

### UPI
- **Source:** Acquiring bank / PSP merchant statements
- **Use:** Retail MSME revenue proxy

### Bureau
- **Source:** CIBIL TransUnion / CRIF / Experian (commercial + consumer promoter)
- **Use:** Promoter discipline, write-offs, DPD

### Google / sentiment
- **Source:** Places API → reviews → NLP (`google_sentiment_score` feature)
- **Low cost** entry point for reputation pillar

### Electricity
- **Source:** Discom bill OCR or utility API
- **Use:** Manufacturing production proxy

## Data refresh cadence (production)

| Source | Suggested frequency |
|--------|---------------------|
| GST | Monthly (post filing) |
| UPI / AA | Daily or weekly |
| EPFO | Monthly |
| Bureau | On application + annual review |
| Courts | Weekly batch |
| Macro | Monthly |

## Files reference

| Path | Purpose |
|------|---------|
| `data/synthetic/profiles/*.json` | Dummy borrower records |
| `scripts/generate_data.py` | Regenerate synthetic portfolio |
| `src/connectors/base.py` | Connector interface |
| `src/connectors/sources.py` | Mock connectors (replace here) |
| `src/features/feature_engineering.py` | Feature definitions |
