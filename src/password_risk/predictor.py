"""Safe local inference wrapper used by the Streamlit interface."""

from __future__ import annotations

from pathlib import Path

import joblib

from .features import extract_numeric_features


def risk_label(score_percent: float) -> str:
    if score_percent > 70:
        return "Weak"
    if score_percent >= 30:
        return "Medium"
    return "Strong"


def guidance(password: str, score_percent: float) -> list[str]:
    features = extract_numeric_features(password)
    tips: list[str] = []
    if len(password) < 15:
        tips.append("Use a longer password or passphrase; 15 or more characters is a good target.")
    if features[10] or features[11]:
        tips.append("Avoid number sequences and keyboard patterns.")
    if features[8] >= 3 or features[9] > 0.35:
        tips.append("Avoid repeated characters or repeated chunks.")
    if not tips and score_percent >= 30:
        tips.append("Choose a unique password generated and stored by a password manager.")
    if score_percent < 30:
        tips.append("Keep this password unique; do not reuse it on another account.")
    return tips[:3]


class PasswordRiskPredictor:
    """Load a trained artifact and predict without persisting user input."""

    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        self.model = joblib.load(self.model_path)

    def evaluate(self, password: str) -> dict[str, object]:
        if not isinstance(password, str):
            raise TypeError("password must be a string")
        if len(password) < 4:
            raise ValueError("Enter at least 4 characters so the model can evaluate a pattern.")
        if len(password) > 64:
            raise ValueError("Enter no more than 64 characters for this prototype.")
        score = float(self.model.predict_proba([password])[0, 1]) * 100
        score = max(0.0, min(100.0, score))
        return {
            "risk_percent": round(score, 1),
            "label": risk_label(score),
            "guidance": guidance(password, score),
        }

