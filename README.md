# Finn. Early Default Prediction

**12-month MSME loan stress early warning** — combining structured alt-data, collection payment timing, bureau/NTC signals, and unstructured text conversion.

**Repository:** https://github.com/arunbhatg/finn-early-default-prediction

**Powered by Finn.** · [Try Finndot AI app](https://play.google.com/store/apps/details?id=com.anomapro.finndot.prd)

---

## Problem

Loan default prediction accuracy currently sits between **16–22%** when relying only on static structured data (bureau snapshots, loan master, basic GST).

## Solution

A predictive model that identifies loan stress **12 months in advance** with **~90% accuracy** by adding:

- **Collection payment timing** — DPD trends, EMI lead/lag days, bounces, broken promise-to-pay
- **Bureau other-loan behaviour** — how the promoter pays non-IDBI facilities
- **NTC alt-data proxies** — GST, UPI, EPFO, AA when no bureau score exists
- **Unstructured → structured NLP features** — reviews, news, RM notes, GST notices, collection field notes

## Underwriter workflow (app)

| Step | Screen | Purpose |
|------|--------|---------|
| ① | **Portfolio** | Active MSME loans with stress badge + loan type |
| ② | **Assessment** | 12m stress probability, risk band, model comparison (18% vs 90%) |
| ③ | **Signals** | Collection charts, bureau other-loans, unstructured evidence |

## Demo cases

| ID | Loan type | Credit file | Typical stress |
|----|-----------|-------------|----------------|
| MSME001 | Term Loan | Bureau | Low |
| MSME002 | Cash Credit | **NTC** | Low–Watch |
| MSME003 | Working Capital | Bureau | **High** — early warning ~12m before default |
| MSME004 | Mudra/PMEGP | **NTC** | Low |

## Streamlit Cloud deploy

| Setting | Value |
|---------|--------|
| **Repository** | `arunbhatg/finn-early-default-prediction` |
| **Branch** | `main` |
| **Main file path** | `streamlit_app.py` |

After each push: **Manage app → Reboot app** (or wait for auto-redeploy).

**Verify deploy:** sidebar should show `Build: 1b00156 · month-on-book UI` and nav tabs **Portfolio · Decision · Evidence** (not Assessment / Signals).

## Quick start

```bash
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_model.py
python scripts/verify_predictions.py
streamlit run app/main.py
```

Open http://localhost:8501 → **Portfolio** → compare **MSME001** vs **MSME003**.

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Early-warning pipeline |
| [docs/EARLY_WARNING.md](docs/EARLY_WARNING.md) | Business case & RM workflow |
| [docs/CONNECTOR_INTEGRATION.md](docs/CONNECTOR_INTEGRATION.md) | CBS loan tape + bureau feeds |
| [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) | Structured + unstructured sources |
| [docs/FINN_ML_Model_Documentation.docx](docs/FINN_ML_Model_Documentation.docx) | **ML model doc (Word)** — target, features, training, scoring |

Regenerate the Word doc after retraining: `python scripts/generate_model_doc.py`

## Tech stack

Python · Streamlit · LightGBM · Plotly · Pandas

## PoC disclaimer

90% accuracy is demonstrated on **curated synthetic portfolio data**. Production requires real NPA labels, out-of-time validation, and model governance.

## License

Hackathon / PoC — internal use.
