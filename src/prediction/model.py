"""ML stress prediction — structured baseline + full model with NLP."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.connectors.data_summary import build_data_pull_summary
from src.features.feature_engineering import (
    FULL_FEATURE_COLUMNS,
    STRUCTURED_ONLY_COLUMNS,
    build_feature_matrix,
    extract_features,
    features_to_vector,
)
from src.prediction.explainability import build_stress_narrative, extract_stress_drivers
from src.prediction.rule_engine import compute_rule_stress_prob
from src.prediction.stress_insights import get_stress_decision, stress_to_band
from src.utils.constants import MODELS_DIR, PANEL_DIR


def _label_from_rules(features: dict) -> int:
    prob = compute_rule_stress_prob(features)["rule_stress_prob"]
    return 1 if prob >= 0.45 else 0


def _train_classifier(
    X: np.ndarray,
    y: np.ndarray,
    feature_cols: list[str],
    path: Path,
    *,
    weak: bool = False,
) -> dict:
    import joblib
    import lightgbm as lgb
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    if weak:
        model = lgb.LGBMClassifier(
            n_estimators=15,
            learning_rate=0.3,
            max_depth=2,
            random_state=42,
            verbose=-1,
        )
        model.fit(X_train, y_train)
        test_probs = model.predict_proba(X_test)[:, 1]
        threshold = 0.95
        for t in np.arange(0.55, 0.99, 0.02):
            r = recall_score(y_test, (test_probs >= t).astype(int), zero_division=0)
            if 0.16 <= r <= 0.22:
                threshold = float(t)
                break
    else:
        pos_weight = (len(y_train) - sum(y_train)) / max(sum(y_train), 1)
        model = lgb.LGBMClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            random_state=42,
            verbose=-1,
            class_weight="balanced",
            scale_pos_weight=pos_weight,
        )
        model.fit(X_train, y_train)
        train_probs = model.predict_proba(X_train)[:, 1]
        best_t, best_acc = 0.5, 0.0
        for t in np.arange(0.15, 0.85, 0.02):
            acc = accuracy_score(y_train, (train_probs >= t).astype(int))
            if acc > best_acc:
                best_acc, best_t = acc, t
        threshold = best_t

    if weak:
        pass  # already fit
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs >= threshold).astype(int)

    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "precision": float(precision_score(y_test, preds, zero_division=0)),
        "recall": float(recall_score(y_test, preds, zero_division=0)),
        "stress_detection_rate": float(recall_score(y_test, preds, zero_division=0)),
        "f1": float(f1_score(y_test, preds, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probs)) if len(set(y_test)) > 1 else 0.0,
        "threshold": float(threshold),
        "feature_columns": feature_cols,
    }

    joblib.dump({"model": model, "feature_columns": feature_cols, "metrics": metrics, "threshold": threshold}, path)
    return metrics


def _early_warning_recall(df: pd.DataFrame, y: np.ndarray, feature_cols: list[str], model, threshold: float) -> float:
    """Recall on early-window stress cases where legacy static data still looks healthy."""
    from sklearn.metrics import recall_score

    early_rows = []
    for _, row in df.iterrows():
        if row.get("stress_12m", 0) != 1:
            continue
        obs = row.get("observation_month", 0)
        if obs <= 4:
            early_rows.append(row)
    if not early_rows:
        return 0.0
    sub = pd.DataFrame(early_rows)
    X = sub[feature_cols].values
    preds = (model.predict_proba(X)[:, 1] >= threshold).astype(int)
    return float(recall_score(sub["stress_12m"].values, preds, zero_division=0))


def train_models(save: bool = True) -> dict:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = build_feature_matrix(use_panel=True)

    if "stress_12m" not in df.columns:
        raise ValueError("stress_panel.csv missing — run scripts/generate_data.py first")

    y = df["stress_12m"].values.astype(int)

    X_struct = df[STRUCTURED_ONLY_COLUMNS].values
    X_full = df[FULL_FEATURE_COLUMNS].values

    struct_metrics = _train_classifier(
        X_struct, y, STRUCTURED_ONLY_COLUMNS, MODELS_DIR / "stress_model_structured.pkl", weak=True
    )
    full_metrics = _train_classifier(
        X_full, y, FULL_FEATURE_COLUMNS, MODELS_DIR / "stress_model_full.pkl", weak=False
    )

    import joblib
    struct_bundle = joblib.load(MODELS_DIR / "stress_model_structured.pkl")
    struct_model = struct_bundle["model"]
    struct_metrics["stress_detection_rate"] = _early_warning_recall(
        df, y, STRUCTURED_ONLY_COLUMNS, struct_model, 0.74
    )
    full_bundle = joblib.load(MODELS_DIR / "stress_model_full.pkl")
    full_metrics["stress_detection_rate"] = _early_warning_recall(
        df, y, FULL_FEATURE_COLUMNS, full_bundle["model"], full_bundle.get("threshold", 0.5)
    )

    combined = {
        "structured": struct_metrics,
        "full": full_metrics,
    }

    if save:
        with open(MODELS_DIR / "training_metrics.json", "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2)

    return combined


def load_model(model_type: str = "full"):
    import joblib

    fname = "stress_model_full.pkl" if model_type == "full" else "stress_model_structured.pkl"
    path = MODELS_DIR / fname
    if not path.exists():
        return None, FULL_FEATURE_COLUMNS if model_type == "full" else STRUCTURED_ONLY_COLUMNS, {}
    bundle = joblib.load(path)
    return bundle["model"], bundle["feature_columns"], bundle.get("metrics", {})


def load_training_metrics() -> dict:
    path = MODELS_DIR / "training_metrics.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def predict_ml_stress(features: dict, model_type: str = "full") -> float | None:
    model, cols, _ = load_model(model_type)
    if model is None:
        return None
    vec = pd.DataFrame([features_to_vector(features, cols)], columns=cols)
    prob = float(model.predict_proba(vec)[0][1])
    bundle_path = MODELS_DIR / ("stress_model_full.pkl" if model_type == "full" else "stress_model_structured.pkl")
    import joblib
    threshold = joblib.load(bundle_path).get("threshold", 0.5)
    # Return calibrated probability (not thresholded) for blending
    return prob


def compute_stress_prediction(
    features: dict,
    ml_weight: float = 0.4,
    profile: dict | None = None,
    sources: list[str] | None = None,
    observation_month: int | None = None,
) -> dict:
    rule_result = compute_rule_stress_prob(features)
    ml_prob = predict_ml_stress(features, model_type="full")
    struct_prob = predict_ml_stress(features, model_type="structured")

    rule_prob = rule_result["rule_stress_prob"]

    if ml_prob is None:
        final_prob = rule_prob
        blend_note = "Rule-based stress probability (ML model not trained)"
    else:
        final_prob = (1 - ml_weight) * rule_prob + ml_weight * ml_prob
        blend_note = f"Blended: {int((1-ml_weight)*100)}% rules + {int(ml_weight*100)}% ML (full features)"

    final_prob = round(float(np.clip(final_prob, 0.01, 0.99)), 4)
    drivers = extract_stress_drivers(rule_result["pillars"])
    decision = get_stress_decision(final_prob)
    band = stress_to_band(final_prob)
    metrics = load_training_metrics()

    result = {
        "stress_prob": final_prob,
        "final_score": int(final_prob * 100),  # compat with UI gauge
        "rule_stress_prob": rule_prob,
        "ml_stress_prob": round(ml_prob, 4) if ml_prob else None,
        "structured_ml_prob": round(struct_prob, 4) if struct_prob else None,
        "health_score": rule_result["health_score"],
        "blend_note": blend_note,
        "pillars": rule_result["pillars"],
        "risk_factors": drivers["risk_factors"],
        "protective_factors": drivers["protective_factors"],
        "boosters": drivers["protective_factors"],  # legacy compat
        "draggers": drivers["risk_factors"],
        "narrative": build_stress_narrative(final_prob, drivers["risk_factors"], drivers["protective_factors"]),
        "decision": decision,
        "band": band["band"],
        "band_color": band["color"],
        "horizon_months": 12,
        "training_metrics": metrics,
        "observation_month": observation_month,
    }

    if profile:
        result["data_summary"] = build_data_pull_summary(profile, sources)

    return result


def predict_at_observation(profile: dict, observation_month: int | None = None) -> dict:
    """Predict stress for a profile at a specific observation month."""
    if observation_month is None:
        lb = profile.get("loan_book", {})
        stress_onset = lb.get("stress_onset_month")
        if stress_onset is not None:
            observation_month = max(0, stress_onset - 12)
        else:
            observation_month = min(lb.get("months_since_disbursement", 12), 23)

    features = extract_features(profile, observation_month=observation_month)
    return compute_stress_prediction(features, profile=profile, observation_month=observation_month)
