"""Auto-bootstrap data and models on first run."""

from src.utils.constants import MODELS_DIR, PROFILES_DIR


def ensure_ready() -> None:
    """Generate synthetic data and train models if missing."""
    profile_count = len(list(PROFILES_DIR.glob("*.json"))) if PROFILES_DIR.exists() else 0

    if profile_count < 4:
        from src.seed_demo import seed_demo_profiles

        seed_demo_profiles()
        profile_count = len(list(PROFILES_DIR.glob("*.json")))

    if profile_count < 50:
        from scripts.generate_data import generate_all

        generate_all()

    if not (MODELS_DIR / "stress_model_full.pkl").exists():
        from src.prediction.model import train_models

        train_models()
