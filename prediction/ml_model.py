"""
Machine-learning integration layer.

The Random Forest is trained OFFLINE by  ml/train_model.py  and saved with Joblib.
Here we only LOAD it (once, then cached in memory) and use predict()/predict_proba().
"""
import json
from functools import lru_cache

import joblib
import pandas as pd
from django.conf import settings

# Same order as used during training.
FEATURES = ["attendance_percentage", "internal_marks", "assignment_score", "quiz_score",
            "midterm_score", "study_hours", "previous_sem_percentage", "backlogs"]

FEATURE_LABELS = {
    "attendance_percentage": "Attendance", "internal_marks": "Internal Marks",
    "assignment_score": "Assignment Score", "quiz_score": "Quiz Score",
    "midterm_score": "Midterm Score", "study_hours": "Study Hours",
    "previous_sem_percentage": "Previous Semester", "backlogs": "Backlogs",
}


class ModelUnavailableError(Exception):
    """Raised when the trained model is missing or cannot be loaded."""


@lru_cache(maxsize=1)
def load_model():
    path = settings.MODEL_PATH
    if not path.exists():
        raise ModelUnavailableError(
            "The trained model file was not found. Run  python ml/train_model.py  first.")
    try:
        return joblib.load(path)
    except Exception as exc:  # corrupted file or scikit-learn version mismatch
        raise ModelUnavailableError(
            "The model file could not be loaded (possibly a scikit-learn version mismatch). "
            "Re-train it with  python ml/train_model.py.") from exc


def risk_level(pass_probability):
    """pass_probability is 0-1. Thresholds live in settings.RISK_THRESHOLDS."""
    t = settings.RISK_THRESHOLDS
    if pass_probability >= t["low"]:
        return "LOW"
    if pass_probability >= t["medium"]:
        return "MEDIUM"
    return "HIGH"


def predict(features):
    """features: dict with the 8 feature names -> dict with label, probabilities (%) and risk."""
    model = load_model()
    try:
        row = pd.DataFrame([[float(features[f]) for f in FEATURES]], columns=FEATURES)
        label = int(model.predict(row)[0])
        proba = model.predict_proba(row)[0]
        pass_p = float(proba[list(model.classes_).index(1)])
    except Exception as exc:
        raise ModelUnavailableError("Prediction failed. Please check the input values.") from exc
    return {
        "prediction": "PASS" if label == 1 else "FAIL",
        "pass_probability": round(pass_p * 100, 2),
        "fail_probability": round((1 - pass_p) * 100, 2),
        "risk_level": risk_level(pass_p),
    }


def _read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def get_metrics():
    return _read_json(settings.METRICS_PATH)


def get_importance():
    """Returns {feature_label: percent} sorted high -> low, or {} if the file is missing."""
    raw = _read_json(settings.IMPORTANCE_PATH) or {}
    return {FEATURE_LABELS.get(k, k): v for k, v in raw.items()}
