# FinHealth Card — Documentation

Technical and business documentation for the MSME alternative-data credit PoC.

| Document | Audience | Contents |
|----------|----------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Engineering, architects | System design, scoring pipeline, deployment |
| [DATA_SOURCES.md](DATA_SOURCES.md) | Engineering, product | Real vs dummy data, connector replacement guide |
| [NTC_MSME.md](NTC_MSME.md) | Business, underwriting, judges | Why alt-data works for New-To-Credit MSMEs |
| [CODE_GUIDE.md](CODE_GUIDE.md) | Developers | Repo layout, modules, how to extend |

## Quick links

- **Live demo:** Deployed on Streamlit Community Cloud (`app/main.py`)
- **GitHub:** https://github.com/arunbhatg/finhealth-card
- **Entry point:** `app/main.py` → underwriter workflow (4 steps)

## One-page summary

FinHealth Card scores **New-To-Credit (NTC) MSMEs** using **10 alternative data connectors** when traditional financials and bureau history are unavailable. A **hybrid engine** (rule-based explainability + LightGBM calibration) produces a **300–900 health score** with pillar breakdown, risk flags, and loan simulation.

**PoC status:** All borrower data is **synthetic** via mock connectors; architecture is production-shaped so real APIs (GSTN, Account Aggregator, EPFO, bureau) can replace mocks without changing scoring logic.
