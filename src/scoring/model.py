"""ML model training and inference."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.features.feature_engineering import FEATURE_COLUMNS, build_feature_matrix
from src.scoring.explainability import build_score_narrative, extract_score_drivers
from src.scoring.rule_engine import compute_rule_score
from src.connectors.data_summary import build_data_pull_summary
from src.utils.constants import MODELS_DIR, SCORE_MAX, SCORE_MIN


def _label_from_rules(features: dict) -> float:
    return compute_rule_score(features)["rule_score"]


def train_model(save: bool = True) -> dict:
    import joblib
    import lightgbm as lgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = build_feature_matrix()
    X = df[FEATURE_COLUMNS].values
    y = np.array([_label_from_rules(row.to_dict()) for _, row in df.iterrows()])
    noise = np.random.normal(0, 15, size=len(y))
    y = np.clip(y + noise, SCORE_MIN, SCORE_MAX)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = lgb.LGBMRegressor(
        n_estimators=120,
        learning_rate=0.08,
        max_depth=5,
        random_state=42,
        verbose=-1,
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y_test, preds))),
        "r2": float(r2_score(y_test, preds)),
    }

    if save:
        joblib.dump({"model": model, "feature_columns": FEATURE_COLUMNS}, MODELS_DIR / "score_model.pkl")

    return metrics


def load_model():
    import joblib

    path = MODELS_DIR / "score_model.pkl"
    if not path.exists():
        return None, FEATURE_COLUMNS
    bundle = joblib.load(path)
    return bundle["model"], bundle["feature_columns"]


def predict_ml_score(features: dict) -> float | None:
    from src.features.feature_engineering import features_to_vector

    model, cols = load_model()
    if model is None:
        return None
    vec = pd.DataFrame([features_to_vector(features, cols)], columns=cols)
    return float(model.predict(vec)[0])


def compute_final_score(
    features: dict,
    ml_weight: float = 0.4,
    profile: dict | None = None,
    sources: list[str] | None = None,
) -> dict:
    rule_result = compute_rule_score(features)
    ml_score = predict_ml_score(features)

    if ml_score is None:
        final = rule_result["rule_score"]
        blend_note = "Rule-based score (ML model not trained)"
    else:
        final = (1 - ml_weight) * rule_result["rule_score"] + ml_weight * ml_score
        blend_note = f"Blended: {int((1-ml_weight)*100)}% rules + {int(ml_weight*100)}% ML"

    final = round(float(np.clip(final, SCORE_MIN, SCORE_MAX)), 0)
    drivers = extract_score_drivers(rule_result["pillars"])

    result = {
        "final_score": final,
        "rule_score": rule_result["rule_score"],
        "ml_score": round(ml_score, 0) if ml_score else None,
        "blend_note": blend_note,
        "pillars": rule_result["pillars"],
        "boosters": drivers["boosters"],
        "draggers": drivers["draggers"],
        "narrative": build_score_narrative(final, drivers["boosters"], drivers["draggers"]),
    }

    if profile:
        result["data_summary"] = build_data_pull_summary(profile, sources)

    return result
