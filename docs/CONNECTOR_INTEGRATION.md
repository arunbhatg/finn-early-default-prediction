# Connector Integration Guide

How to connect each data source — what is **live today**, what is **mock**, and the **production path**.

---

## Status overview (PoC)

| # | Source | App status | Public data available? | Production path |
|---|--------|------------|--------------------------|-----------------|
| 1 | **Macro / RBI** | 🟢 **LIVE** | Yes — [Indian Data Project](https://indiandataproject.org/open-data) | Already integrated |
| 2 | **Weather / rainfall** | 🟢 **LIVE** | Yes — [Open-Meteo](https://open-meteo.com/) (no API key) | Already integrated |
| 3 | **Google Business** | 🟡 **Optional LIVE** | Yes — Google Places API (API key required) | Set `GOOGLE_PLACES_API_KEY` |
| 4 | **Sector growth** | 🟡 **STATIC** | Partial — RBI sectoral bulletins, MOSPI | ETL from published tables |
| 5 | **GST** | ⚪ Mock | No free public API | GSP / GST Suvidha Provider |
| 6 | **UPI** | ⚪ Mock | No | Bank merchant / NPCI (licensed) |
| 7 | **Account Aggregator** | ⚪ Mock | No | RBI AA — FIU + Sahamati |
| 8 | **EPFO** | ⚪ Mock | No (API Setu for specific use cases) | EPFO employer API / API Setu |
| 9 | **Promoter bureau** | ⚪ Mock | No | CIBIL / CRIF / Experian |
| 10 | **Courts** | ⚪ Mock | Partial — eCourts (no clean API) | Legal data aggregators |
| 11 | **Electricity** | ⚪ Mock | No | Discom portal / bill OCR |
| 12 | **Investment / MCA** | ⚪ Mock | Partial — MCA21 public filings | MCA API / data.gov.in |

**Live without API key:** 2 (Macro, Weather)  
**Live with API key:** +1 (Google Places)  
**Mock (borrower-specific):** 7

---

## Architecture: how connectors plug in

```
                    ┌─────────────────────┐
                    │  enrich_profile()   │
                    │  (public overlays)  │
                    └──────────┬──────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│  BaseConnector.fetch(profile)  — per source               │
│  Mock: read profile["gst"] from JSON                      │
│  Live: HTTP API → map to same JSON schema                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ extract_features()  │
                    │ (unchanged)         │
                    └─────────────────────┘
```

**Rule:** Live connectors must return the **same schema** as synthetic data. Map API fields in the connector only.

Code locations:
- Live public: `src/connectors/live/`
- Enrichment orchestrator: `src/connectors/enrichment.py`
- Mock connectors: `src/connectors/sources.py`
- Feature pipeline: `src/features/feature_engineering.py`

---

## 1. Macro / RBI (LIVE ✅)

### Current implementation
- **File:** `src/connectors/live/macro_public.py`
- **Primary URL:** `https://indiandataproject.org/data/rbi/2025-26/summary.json`
- **Fallback:** `oriz-rbi-rates-api` GitHub raw JSON
- **Fields used:** `repoRate`, `cpi`, `stance`

### What you get
- Live repo rate and RBI policy stance on every case assessment
- Displayed in Macro summary and connector status panel

### Production upgrade
- Schedule daily ETL from RBI DBIE or internal treasury feed
- Store in Redis/DB; connector reads from cache

---

## 2. Weather / Rainfall (LIVE ✅)

### Current implementation
- **File:** `src/connectors/live/weather_public.py`
- **API:** Open-Meteo forecast API (free, no key)
- **Input:** MSME city → lat/lon lookup
- **Output:** 30-day precipitation → `monsoon_index_pct` feature

### Production upgrade
- IMD gridded rainfall for agri MSMEs
- Sector-specific weather overlays (textiles humidity, etc.)

---

## 3. Google Business (OPTIONAL LIVE)

### Enable live reviews
1. Get [Google Places API](https://developers.google.com/maps/documentation/places/web-service) key
2. Set environment variable:
   ```bash
   GOOGLE_PLACES_API_KEY=your_key_here
   ```
   Or in Streamlit Cloud → Secrets:
   ```toml
   GOOGLE_PLACES_API_KEY = "your_key"
   ```
3. Restart app — connector searches by business name + city

### File
- `src/connectors/live/google_places.py`

### Cost note
- Places API is pay-per-use; enable billing on GCP project

---

## 4. GST

### Why mock in PoC
GST return data is **not publicly available**. Access requires taxpayer consent via licensed GSP.

### Production integration

| Step | Action |
|------|--------|
| 1 | Register as GSP or partner with ClearTax / IRIS / Cygnet / etc. |
| 2 | Obtain GSTIN + OTP consent from MSME |
| 3 | Fetch GSTR-1, GSTR-3B via GSP API |
| 4 | Map to schema: `monthly_turnover_lakhs`, `filing_status`, `payment_delays_count` |

### Reference APIs
- GST Suvidha Provider ecosystem
- E-Invoice IRP data APIs (with consent): `einvoice6.gst.gov.in`
- GSTIN validation (master only, not returns): sandbox `get-gstin-details`

### Sample connector skeleton

```python
# src/connectors/live/gst_live.py
class GSTLiveConnector(BaseConnector):
    def fetch(self, profile: dict) -> dict:
        gstin = profile["gstin"]
        raw = gsp_client.get_returns(gstin, months=24)
        return {
            "monthly_turnover_lakhs": [...],
            "filing_status": [...],
            "payment_delays_count": ...,
            "b2b_sales_ratio": ...,
        }
```

### Consent
- Digital consent artefact + GSTIN OTP
- Store consent ID for audit

---

## 5. Account Aggregator (AA)

### Framework
- RBI Account Aggregator ecosystem ([Sahamati](https://sahamati.org.in/))
- FIU (Financial Information User) = bank/fintech
- FIP (Financial Information Provider) = banks

### Flow
```
MSME consent → AA consent artefact → FIP fetch → normalised FI data
```

### Map to schema
| AA field | Profile key |
|----------|-------------|
| Monthly credits | `aa.monthly_credits_lakhs` |
| Monthly debits | `aa.monthly_debits_lakhs` |
| Closing balance | `aa.monthly_closing_balance_lakhs` |
| ABB | `aa.abb_lakhs` |
| EMI tracking | `aa.emi_on_time_rate`, `aa.bounce_count_12m` |

### Steps to go live
1. Register as FIU with Sahamati
2. Integrate AA SDK / API (Setu, Finvu, OneMoney, etc.)
3. Implement consent UI (replace mock checkboxes)
4. Parse bank statement FI types (deposit, term deposit)

---

## 6. UPI

### Why mock
NPCI does not offer public merchant transaction APIs.

### Production paths
| Path | Provider |
|------|----------|
| Acquiring bank | HDFC, ICICI, Axis merchant statements |
| Payment aggregator | Razorpay, PayU, PhonePe Business |
| Account Aggregator | UPI credits visible in bank FI data |

### Schema
```json
{
  "monthly_volume_lakhs": [],
  "monthly_txn_count": [],
  "p2m_ratio": 0.82,
  "failed_txn_rate": 0.01
}
```

---

## 7. EPFO

### Production paths
| Path | Notes |
|------|-------|
| API Setu | `apisetu.gov.in/epfindia` — employer verification (govt gateway) |
| Direct EPFO | Establishment login / authorised third party |
| HR payroll SaaS | Keka, greytHR export |

### Schema
```json
{
  "employee_count": [],
  "monthly_wage_bill_lakhs": [],
  "contribution_status": ["paid", "delayed", ...]
}
```

### Use case
Validates declared turnover vs wage bill; detects payroll stress.

---

## 8. Promoter Bureau (CIBIL / CRIF)

### Production path
1. Membership with TransUnion CIBIL / CRIF High Mark / Experian
2. Permissible purpose: credit underwriting
3. Pull consumer score for promoter + commercial score if available

### Schema
```json
{
  "promoter_name": "...",
  "cibil_score": 750,
  "dpd_12m": 0,
  "write_offs_36m": 0,
  "credit_utilization": 0.35
}
```

### NTC note
Many MSMEs have **no commercial bureau** — promoter **consumer** CIBIL is often the only bureau signal.

---

## 9. Court / Litigation

### Production paths
| Provider type | Examples |
|---------------|----------|
| Legal aggregators | Probe42, Crediwatch, Livelaw data feeds |
| eCourts | National Judicial Data Grid (limited programmatic access) |
| MCA | Director disqualification, struck-off companies |

### Schema
```json
{
  "civil_cases": 0,
  "criminal_cases": 0,
  "insolvency_petitions": 0,
  "total_outstanding_litigation_lakhs": 0
}
```

---

## 10. Electricity

### Production paths
| Path | Notes |
|------|-------|
| Discom API | MSEDCL, BESCOM (varies by state) |
| Bill OCR | Upload electricity bill → extract kWh |
| IoT / smart meter | Industrial consumers |

### Use case
Manufacturing production proxy — kWh trend vs GST turnover.

---

## 11. Investment / MCA

### Partial public data
- MCA21 portal — company charges, director info
- IP India — patent search (public)

### Production path
1. MCA API or aggregator (Probe42, Tofler)
2. Map `capex_lakhs_12m`, `patents_count`, `govt_scheme_beneficiary`

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `GOOGLE_PLACES_API_KEY` | Enable live Google reviews |
| `USE_LIVE_CONNECTORS` | Future flag for all live connectors |
| `GSP_API_KEY` | GST live (production) |
| `AA_FIU_CLIENT_ID` | Account Aggregator (production) |
| `CIBIL_MEMBER_ID` | Bureau pull (production) |

### Streamlit Cloud secrets example

```toml
GOOGLE_PLACES_API_KEY = "AIza..."
```

---

## Recommended rollout phases

### Phase 1 — Hackathon / PoC (now)
- ✅ Macro (live)
- ✅ Weather (live)
- Optional Google Places
- Mock borrower data

### Phase 2 — Pilot (3–6 months)
1. GST via GSP
2. Account Aggregator
3. Promoter bureau
4. UPI via bank or AA

### Phase 3 — Scale
5. EPFO
6. Courts aggregator
7. Electricity OCR
8. MCA / investment

---

## Testing live connectors

```bash
python -c "
from src.connectors.live.macro_public import fetch_live_macro
from src.connectors.live.weather_public import fetch_live_weather
print('Macro:', fetch_live_macro())
print('Weather:', fetch_live_weather('Pune'))
"
```

---

## Switching mock → live (checklist)

- [ ] Implement `*_live.py` connector returning same schema
- [ ] Add env var + secrets
- [ ] Update `src/connectors/enrichment.py` or `sources.py` factory
- [ ] Record API fixtures for offline tests
- [ ] Update connector status UI (auto-detects `live` flag)
- [ ] Document consent flow for regulated sources
- [ ] Retrain ML model on real portfolio labels

---

## Related docs

- [DATA_SOURCES.md](DATA_SOURCES.md) — Real vs dummy summary
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [CODE_GUIDE.md](CODE_GUIDE.md) — Where to edit code
