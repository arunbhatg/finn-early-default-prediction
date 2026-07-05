"""Verify early-warning predictions on demo cases."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.connectors.base import load_profile
from src.prediction.model import load_training_metrics, predict_at_observation

print("\n=== Training metrics ===")
metrics = load_training_metrics()
if metrics:
    s = metrics.get("structured", {})
    f = metrics.get("full", {})
    print(f"Structured-only accuracy: {s.get('accuracy', 0)*100:.1f}%")
    print(f"Full model accuracy:      {f.get('accuracy', 0)*100:.1f}%")

for mid in ["MSME001", "MSME002", "MSME003", "MSME004"]:
    profile = load_profile(mid)
    result = predict_at_observation(profile)
    obs = result.get("observation_month", "—")
    prob = result["stress_prob"]
    band = result["band"]
    print(f"\n=== {mid} @ month {obs} — {band} ({prob*100:.0f}% stress in 12m) ===")
    print(result["narrative"])
    if result.get("risk_factors"):
        print("RISKS:", [f"{d['factor']} ({d['value']})".replace("\u2605", "*") for d in result["risk_factors"][:3]])
    if mid == "MSME003":
        assert prob >= 0.45, f"MSME003 should show elevated stress, got {prob}"
        print("OK MSME003 early warning validated (~12 months ahead of default)")
