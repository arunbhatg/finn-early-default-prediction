# FinHealth Card

**Alternative-data credit assessment for New-To-Credit (NTC) MSMEs** — when traditional financials and bureau history are unavailable.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

**Repository:** https://github.com/arunbhatg/finhealth-card

---

## What it does

Scores MSME creditworthiness using **10 digital data sources** (GST, UPI, Account Aggregator, EPFO, Google sentiment, promoter bureau, courts, electricity, macro, investment) and produces:

- **Financial Health Score** (300–900, CIBIL-like scale)
- **Credit recommendation** (Approve / Review / Decline)
- **Explainable pillars** + risk flags for underwriters
- **Indicative loan offer** (limit, rate, tenure)

## Underwriter workflow (app)

| Step | Screen | Purpose |
|------|--------|---------|
| ① | **Select MSME Case** | Pick demo borrower with visible score/decision preview |
| ② | **Credit Decision** | Score, recommendation, key metrics, drivers, flags |
| ③ | **Evidence & Trends** | GST, UPI, bank, payroll charts |
| ④ | **Loan Offer** | Limit and pricing simulation |

## Quick start

```bash
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_model.py
streamlit run app/main.py
```

Open http://localhost:8501 → **① Select MSME Case** → compare **MSME001** vs **MSME003**.

## Deploy (free)

1. Push to GitHub
2. [share.streamlit.io](https://share.streamlit.io) → New app
3. Main file: `app/main.py`

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design & scoring pipeline |
| [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) | Real vs dummy data & API replacement |
| [docs/NTC_MSME.md](docs/NTC_MSME.md) | Business case for NTC MSMEs |
| [docs/CODE_GUIDE.md](docs/CODE_GUIDE.md) | Code layout & extension guide |

## Demo cases

| ID | Profile | Typical score | Decision |
|----|---------|---------------|----------|
| MSME001 | Manufacturer, Pune | ~740 | Approve |
| MSME002 | Retail kirana, Ahmedabad | ~720 | Approve |
| MSME003 | Distressed trader, Delhi | ~460 | Decline |
| MSME004 | Agri-input, Nagpur | ~705 | Approve |

## Tech stack

Python · Streamlit · LightGBM · Plotly · Pandas

## PoC disclaimer

All borrower data is **synthetic**. Architecture supports production connectors (GSTN, AA, bureau) — see [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).

## License

Hackathon / PoC — IDBI internal use.
