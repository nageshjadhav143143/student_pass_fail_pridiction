"""
train_model.py - Student Pass/Fail Prediction System (Random Forest)

Run from the project root:   python ml/train_model.py

Steps: generate/load data -> clean -> EDA -> split -> compare models
       -> tune Random Forest -> evaluate -> save model, metrics, charts.

NOTE: The dataset is SYNTHETIC (generated below), not real student data.
"""
import json
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")  # no GUI needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, make_scorer,
                             precision_score, recall_score, roc_auc_score,
                             roc_curve)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

ML_DIR = Path(__file__).resolve().parent
CHART_DIR = ML_DIR.parent / "static" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

DATA_PATH = ML_DIR / "student_data.csv"
MODEL_PATH = ML_DIR / "random_forest_model.pkl"
METRICS_PATH = ML_DIR / "model_metrics.json"
IMPORTANCE_PATH = ML_DIR / "feature_importance.json"

FEATURES = ["attendance_percentage", "internal_marks", "assignment_score",
            "quiz_score", "midterm_score", "study_hours",
            "previous_sem_percentage", "backlogs"]
TARGET = "final_result"  # 1 = PASS, 0 = FAIL
# Valid ranges (min, max). Final exam marks are deliberately NOT a feature.
RANGES = {"attendance_percentage": (0, 100), "internal_marks": (0, 100),
          "assignment_score": (0, 100), "quiz_score": (0, 100),
          "midterm_score": (0, 100), "study_hours": (0, 24),
          "previous_sem_percentage": (0, 100), "backlogs": (0, 20)}


# ------------------------------------------------------------------ 1. DATA
def generate_dataset(n=1200, seed=42):
    """Synthetic data: a hidden 'ability' drives the scores; noise keeps it realistic."""
    rng = np.random.default_rng(seed)
    ability = rng.normal(0, 1, n)

    def score(base, slope, noise):
        return np.clip(base + slope * ability + rng.normal(0, noise, n), 0, 100)

    df = pd.DataFrame({
        "attendance_percentage": score(76, 9, 9),
        "internal_marks": score(62, 14, 10),
        "assignment_score": score(68, 12, 11),
        "quiz_score": score(60, 13, 12),
        "midterm_score": score(55, 15, 11),
        "study_hours": np.clip(3 + 1.2 * ability + rng.normal(0, 1.4, n), 0, 12),
        "previous_sem_percentage": score(64, 12, 9),
        "backlogs": np.clip(np.round(rng.poisson(np.exp(-0.9 - 0.7 * ability))), 0, 8),
    })
    logit = (0.045 * (df.attendance_percentage - 70)
             + 0.040 * (df.internal_marks - 55)
             + 0.020 * (df.assignment_score - 60)
             + 0.020 * (df.quiz_score - 55)
             + 0.035 * (df.midterm_score - 50)
             + 0.15 * (df.study_hours - 3)
             + 0.030 * (df.previous_sem_percentage - 60)
             - 0.60 * df.backlogs
             - np.where(df.attendance_percentage < 60, 1.2, 0)  # low-attendance penalty
             + 0.8)
    logit += rng.normal(0, 1.0, n)  # random real-world variation
    df[TARGET] = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    for c in FEATURES:
        df[c] = df[c].round(1) if c != "backlogs" else df[c].astype(int)
    return df


def load_or_create_data():
    if DATA_PATH.exists():
        print(f"Loading dataset: {DATA_PATH}")
        return pd.read_csv(DATA_PATH)
    print("No dataset found - generating SYNTHETIC dataset.")
    df = generate_dataset()
    df.to_csv(DATA_PATH, index=False)
    return df


def clean_data(df):
    print("\n--- Cleaning ---")
    print("Missing values:\n", df.isna().sum()[lambda s: s > 0].to_string() or "none")
    before = len(df)
    df = df.drop_duplicates().dropna().copy()
    print(f"Removed {before - len(df)} duplicate/missing rows")
    # Invalid values: drop rows outside valid ranges
    mask = pd.Series(True, index=df.index)
    for col, (lo, hi) in RANGES.items():
        mask &= df[col].between(lo, hi)
    mask &= df[TARGET].isin([0, 1])
    print(f"Removed {(~mask).sum()} rows with invalid values")
    df = df[mask].copy()
    # Outliers: cap study_hours using the IQR rule (other columns are bounded scores)
    q1, q3 = df.study_hours.quantile([.25, .75])
    df["study_hours"] = df.study_hours.clip(upper=q3 + 1.5 * (q3 - q1))
    return df.reset_index(drop=True)


# ------------------------------------------------------------------ 2. EDA
def run_eda(df):
    print("\n--- EDA ---")
    print(df.describe().round(2).to_string())
    counts = df[TARGET].value_counts().sort_index()
    print("\nClass distribution (0=FAIL, 1=PASS):", counts.to_dict())

    plt.figure(figsize=(5, 4))
    sns.barplot(x=["FAIL", "PASS"], y=counts.values, hue=["FAIL", "PASS"],
                palette=["#ef4444", "#22c55e"], legend=False)
    plt.title("Class Distribution"); plt.ylabel("Students")
    plt.tight_layout(); plt.savefig(CHART_DIR / "class_distribution.png", dpi=120); plt.close()

    plt.figure(figsize=(8, 6))
    sns.heatmap(df.corr(), annot=True, fmt=".2f", cmap="coolwarm", square=True)
    plt.title("Correlation Matrix")
    plt.tight_layout(); plt.savefig(CHART_DIR / "correlation_heatmap.png", dpi=120); plt.close()


# --------------------------------------------------------------- 3. MODELS
def metrics_for(y_true, y_pred, y_prob):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_prob),
        # FAIL class (0) is the one we most need to catch
        "fail_recall": recall_score(y_true, y_pred, pos_label=0, zero_division=0),
        "fail_precision": precision_score(y_true, y_pred, pos_label=0, zero_division=0),
        "fail_f1": f1_score(y_true, y_pred, pos_label=0, zero_division=0),
    }


def main():
    df = clean_data(load_or_create_data())
    run_eda(df)

    X, y = df[FEATURES], df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"\nTrain: {len(X_train)}  Test: {len(X_test)}")

    # class_weight="balanced" handles any class imbalance (no resampling needed)
    models = {
        # Logistic Regression is distance/gradient based, so it gets scaling.
        "Logistic Regression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced")),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=6, class_weight="balanced", random_state=42),
    }

    # Random Forest: tune with 5-fold CV, optimising FAIL-class F1 (not just accuracy)
    grid = GridSearchCV(
        RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=-1),
        param_grid={"n_estimators": [100, 200],
                    "max_depth": [6, 10, None],
                    "min_samples_split": [2, 10],
                    "min_samples_leaf": [1, 4],
                    "max_features": ["sqrt", None]},
        scoring=make_scorer(f1_score, pos_label=0),
        cv=StratifiedKFold(5, shuffle=True, random_state=42), n_jobs=-1)
    grid.fit(X_train, y_train)
    print("Best RF params:", grid.best_params_)
    print(f"Best CV FAIL-F1: {grid.best_score_:.3f}")
    models["Random Forest"] = grid.best_estimator_

    results, probs = {}, {}
    for name, model in models.items():
        if name != "Random Forest":
            model.fit(X_train, y_train)
        pred = model.predict(X_test)
        probs[name] = model.predict_proba(X_test)[:, 1]
        results[name] = metrics_for(y_test, pred, probs[name])

    comp = pd.DataFrame(results).T[["accuracy", "precision", "recall", "f1_score", "fail_recall"]]
    print("\n--- Model comparison (test set) ---")
    print(comp.round(4).to_string())

    rf = models["Random Forest"]
    rf_pred = rf.predict(X_test)
    print("\n--- Random Forest classification report ---")
    print(classification_report(y_test, rf_pred, target_names=["FAIL", "PASS"]))
    cm = confusion_matrix(y_test, rf_pred)

    # ---------------------------------------------------------- charts
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["FAIL", "PASS"], yticklabels=["FAIL", "PASS"])
    plt.xlabel("Predicted"); plt.ylabel("Actual"); plt.title("Confusion Matrix - Random Forest")
    plt.tight_layout(); plt.savefig(CHART_DIR / "confusion_matrix.png", dpi=120); plt.close()

    plt.figure(figsize=(6, 5))
    for name in models:
        fpr, tpr, _ = roc_curve(y_test, probs[name])
        plt.plot(fpr, tpr, label=f"{name} (AUC={results[name]['roc_auc']:.2f})")
    plt.plot([0, 1], [0, 1], "k--"); plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate"); plt.title("ROC Curve"); plt.legend()
    plt.tight_layout(); plt.savefig(CHART_DIR / "roc_curve.png", dpi=120); plt.close()

    comp[["accuracy", "precision", "recall", "f1_score"]].plot(
        kind="bar", figsize=(8, 5), ylim=(0, 1))
    plt.title("Model Comparison"); plt.xticks(rotation=0); plt.legend(loc="lower right")
    plt.tight_layout(); plt.savefig(CHART_DIR / "model_comparison.png", dpi=120); plt.close()

    importance = dict(sorted(zip(FEATURES, (rf.feature_importances_ * 100).round(2).tolist()),
                             key=lambda kv: kv[1], reverse=True))
    plt.figure(figsize=(7, 5))
    sns.barplot(x=list(importance.values()), y=list(importance.keys()),
                hue=list(importance.keys()), palette="viridis", legend=False)
    plt.xlabel("Importance (%)"); plt.title("Random Forest Feature Importance")
    plt.tight_layout(); plt.savefig(CHART_DIR / "feature_importance.png", dpi=120); plt.close()

    # ---------------------------------------------------------- save
    joblib.dump(rf, MODEL_PATH)
    IMPORTANCE_PATH.write_text(json.dumps(importance, indent=2))
    out = {
        "algorithm": "Random Forest Classifier",
        "n_estimators": int(rf.n_estimators),
        "best_params": {k: v for k, v in grid.best_params_.items()},
        "training_records": int(len(X_train)),
        "total_records": int(len(df)),
        "test_records": int(len(X_test)),
        "n_features": len(FEATURES),
        "features": FEATURES,
        "data_source": "synthetic",
        "confusion_matrix": cm.tolist(),
        "random_forest": {k: round(v, 4) for k, v in results["Random Forest"].items()},
        "comparison": {n: {k: round(v, 4) for k, v in r.items()} for n, r in results.items()},
    }
    METRICS_PATH.write_text(json.dumps(out, indent=2))
    print(f"\nSaved: {MODEL_PATH.name}, {METRICS_PATH.name}, {IMPORTANCE_PATH.name}")
    print("Feature importance (%):", importance)


if __name__ == "__main__":
    main()
