"""Train structured baseline + full stress prediction models."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.prediction.model import train_models

if __name__ == "__main__":
    metrics = train_models()
    s = metrics["structured"]
    f = metrics["full"]
    print("\n=== Model comparison (12-month stress prediction) ===")
    print(f"Structured-only stress detection: {s['stress_detection_rate']*100:.1f}%  (accuracy={s['accuracy']*100:.1f}%)")
    print(f"Full model stress detection:       {f['stress_detection_rate']*100:.1f}%  (accuracy={f['accuracy']*100:.1f}%)")
