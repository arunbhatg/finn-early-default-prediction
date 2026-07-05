# Code Guide

## Repository layout

```
finhealth-card/
├── app/                          # Streamlit application
│   ├── main.py                   # Entry point, navigation, bootstrap
│   ├── components/
│   │   ├── widgets.py            # Gauges, progress bars
│   │   └── underwriter.py        # Decision panels, charts, demo cards
│   └── views/
│       ├── cases.py              # ① Select MSME Case
│       ├── decision.py           # ② Credit Decision (primary)
│       ├── evidence.py           # ③ Evidence & Trends (plots)
│       ├── loan.py               # ④ Loan Offer
│       ├── onboarding.py         # Optional consent flow
│       └── _helpers.py           # assess_msme(), load_case()
│
├── src/
│   ├── connectors/
│   │   ├── base.py               # BaseConnector, load_profile()
│   │   ├── sources.py            # 10 mock connectors
│   │   └── data_summary.py       # Human-readable source summaries
│   ├── features/
│   │   └── feature_engineering.py # FEATURE_COLUMNS, extract_features()
│   ├── scoring/
│   │   ├── rule_engine.py        # 5-pillar explainable rules
│   │   ├── model.py              # LightGBM train + compute_final_score()
│   │   ├── explainability.py     # Boosters / draggers
│   │   ├── underwriter_insights.py # Flags, decisions, metrics
│   │   └── loan_simulator.py     # Indicative loan pricing
│   ├── utils/
│   │   ├── constants.py          # Weights, personas, macro
│   │   └── helpers.py            # score_to_grade, yoy_growth, etc.
│   ├── bootstrap.py              # First-run data + model setup
│   └── seed_demo.py              # Minimal demo profiles
│
├── data/
│   ├── synthetic/profiles/       # MSME001–MSME075 JSON
│   ├── synthetic/msme_master.csv
│   └── models/score_model.pkl    # Trained LightGBM
│
├── scripts/
│   ├── generate_data.py          # Synthetic portfolio generator
│   ├── train_model.py            # Train and save model
│   └── verify_scores.py          # CLI score check
│
├── docs/                         # This documentation
├── requirements.txt
└── README.md
```

## Key flows

### 1. App startup
`app/main.py` → `ensure_ready()` → generates data / trains model if missing.

### 2. Case assessment
```
load_profile(msme_id)
  → extract_features(profile)
  → compute_final_score(features)
  → extract_score_drivers() + build_data_pull_summary()
  → session_state
```

### 3. Underwriter UI
`views/decision.py` reads `session_state` and renders:
- `render_decision_header()` — score + APPROVE/REVIEW/DECLINE
- `render_key_metrics_row()` — 6 KPIs
- Driver chart + pillar chart
- `render_risk_flags()` — red/amber/green

## Extension points

### Add a new data source

1. Add schema to `scripts/generate_data.py` → `build_profile()`
2. Create `XyzConnector` in `src/connectors/sources.py`
3. Add summariser in `src/connectors/data_summary.py`
4. Add features in `src/features/feature_engineering.py` → `FEATURE_COLUMNS`
5. Add pillar logic in `src/scoring/rule_engine.py` if needed
6. Retrain: `python scripts/train_model.py`

### Swap mock for live API

See [DATA_SOURCES.md](DATA_SOURCES.md). Only change connector `fetch()` — keep output schema identical.

### Change score weights

Edit `PILLAR_WEIGHTS` in `src/utils/constants.py` and pillar logic in `rule_engine.py`.

## Running locally

```bash
pip install -r requirements.txt
python scripts/generate_data.py   # if data/ missing
python scripts/train_model.py     # if model missing
streamlit run app/main.py
```

## Testing scores

```bash
python scripts/verify_scores.py
```

## Deployment

- **Streamlit Cloud:** Main file `app/main.py`
- **Secrets:** `.streamlit/secrets.toml` for API keys (not committed)
- **Model:** Committed at `data/models/score_model.pkl` for fast cold start

## Dependencies

| Package | Role |
|---------|------|
| streamlit | UI |
| pandas / numpy | Data |
| lightgbm / scikit-learn | ML |
| plotly | Charts |
| faker | Synthetic data generation |
| joblib | Model persistence |

## Conventions

- **Features** are flat dicts keyed by `FEATURE_COLUMNS` names
- **Profiles** are nested JSON per MSME (gst, upi, aa, …)
- **Connectors** return raw source blobs; features derived in one place
- **UI** does not embed business rules — use `src/scoring/`
