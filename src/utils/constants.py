"""Constants, sector data, and early-warning configuration."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
SYNTHETIC_DIR = DATA_DIR / "synthetic"
PROFILES_DIR = SYNTHETIC_DIR / "profiles"
PANEL_DIR = SYNTHETIC_DIR / "panels"
MODELS_DIR = DATA_DIR / "models"

PREDICTION_HORIZON_MONTHS = 12

LOAN_TYPES = [
    "Working Capital",
    "Term Loan",
    "Cash Credit",
    "LAP",
    "Equipment Finance",
    "Mudra/PMEGP",
    "Supply Chain Finance",
]

STRESS_BANDS = [
    (0.70, "Critical", "#991B1B"),
    (0.45, "High", "#C2410C"),
    (0.25, "Watch", "#854D0E"),
    (0.0, "Low", "#166534"),
]

PILLAR_WEIGHTS = {
    "repayment": 0.30,
    "cashflow": 0.25,
    "bureau_ntc": 0.20,
    "reputation_nlp": 0.15,
    "context": 0.10,
}

SOURCE_WEIGHTS = {
    "loan_tape": 0.18,
    "collections": 0.22,
    "gst": 0.12,
    "upi": 0.08,
    "aa": 0.12,
    "epfo": 0.06,
    "google": 0.06,
    "bureau": 0.10,
    "courts": 0.04,
    "electricity": 0.02,
}

SECTOR_GROWTH = {
    "Manufacturing": 6.2,
    "Retail": 8.5,
    "Services": 7.1,
    "Agri-Input": 4.8,
    "Textiles": -1.5,
    "Pharma": 9.3,
    "Food Processing": 5.6,
    "Logistics": 7.8,
}

MACRO_INDICATORS = {
    "repo_rate": 6.50,
    "gdp_growth": 6.8,
    "manufacturing_pmi": 52.4,
    "inflation_cpi": 5.1,
    "msme_sentiment_index": 58.2,
}

FINN_SCORE_LABEL = "FINN. Stress Risk (12m)"

DEMO_PERSONAS = {
    "MSME001": {
        "name": "Sharma Precision Works",
        "story": "Term loan — healthy collections, strong bureau track on other facilities",
        "sector": "Manufacturing",
        "city": "Pune",
        "state": "Maharashtra",
        "loan_type": "Term Loan",
        "is_ntc": False,
    },
    "MSME002": {
        "name": "Patel Kirana & General Store",
        "story": "Cash credit — NTC promoter, alt-data substitutes for thin bureau file",
        "sector": "Retail",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "loan_type": "Cash Credit",
        "is_ntc": True,
    },
    "MSME003": {
        "name": "Gupta Trading Company",
        "story": "Working capital — deteriorating payment timing, bureau DPD on other loans",
        "sector": "Retail",
        "city": "Delhi",
        "state": "Delhi",
        "loan_type": "Working Capital",
        "is_ntc": False,
    },
    "MSME004": {
        "name": "Krishi Mitra Agro Supplies",
        "story": "Mudra loan — NTC agri dealer, GST/UPI payment discipline compensates",
        "sector": "Agri-Input",
        "city": "Nagpur",
        "state": "Maharashtra",
        "loan_type": "Mudra/PMEGP",
        "is_ntc": True,
    },
}

DEMO_LOAN_TYPE_MAP = {
    "MSME001": "Term Loan",
    "MSME002": "Cash Credit",
    "MSME003": "Working Capital",
    "MSME004": "Mudra/PMEGP",
}
