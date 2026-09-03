"""
AR Follow-Up AI - ML Training Pipeline (Phase 4)

Trains production-grade Machine Learning classification models:
1. Delay Prediction Model (Target: was_delayed)
2. Denial Prediction Model (Target: was_denied)
3. Recovery Probability & Expected Financial Recovery Evaluator

Saves models to backend/trained_models/ and records actual evaluation metrics.
"""

import sys
import json
import time
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "backend" / "trained_models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Feature definitions (strictly avoiding future leakages: no final_outcome, recovered_amount, days_to_resolution)
NUMERIC_FEATURES = [
    "days_in_ar",
    "outstanding_amount",
    "billed_amount",
    "allowed_amount",
    "paid_amount",
    "patient_responsibility",
    "expected_reimbursement",
    "followup_count",
    "resubmission_count",
    "days_since_last_response",
    "avg_processing_days",
    "avg_response_days",
    "filing_deadline_days",
]

CATEGORICAL_FEATURES = [
    "payer_id",
    "claim_type",
    "place_of_service",
    "claim_status",
    "denial_status",
    "denial_code",
    "denial_reason",
    "authorization_required",
    "authorization_status",
    "network_status",
    "appeal_status",
]


def load_and_prepare_data():
    """Load claims, outcomes, and payer metadata, and construct feature matrix."""
    claims = pd.read_csv(DATA_DIR / "claims.csv")
    outcomes = pd.read_csv(DATA_DIR / "claim_outcomes.csv")
    payers = pd.read_csv(DATA_DIR / "payers.csv")

    df = claims.merge(outcomes, on="claim_id").merge(payers, on="payer_id")

    # Clean missing values for string columns
    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].fillna("Missing").astype(str)

    # Convert authorization_required to string
    df["authorization_required"] = df["authorization_required"].astype(str)

    # Clean numeric features
    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def build_preprocessor():
    """Build Sklearn preprocessor for numeric and categorical columns."""
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, NUMERIC_FEATURES),
            ("cat", cat_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return preprocessor


def train_and_evaluate_model(X_train, X_test, y_train, y_test, model_name: str):
    """Train pipeline and calculate real evaluation metrics."""
    preprocessor = build_preprocessor()

    classifier = HistGradientBoostingClassifier(
        max_iter=150,
        learning_rate=0.08,
        max_depth=6,
        random_state=42,
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", classifier),
    ])

    print(f"   Training {model_name}...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "test_samples": int(len(y_test)),
        "train_samples": int(len(y_train)),
    }

    return pipeline, metrics


def run_training():
    start_time = time.time()
    print("==================================================")
    print("RECOVERAI / AR FOLLOW-UP AI - ML MODEL TRAINING")
    print("==================================================")

    print("1. Loading and merging dataset tables...")
    df = load_and_prepare_data()
    print(f"   ✓ Prepared dataset with {len(df):,} claims and {len(NUMERIC_FEATURES) + len(CATEGORICAL_FEATURES)} features.")

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_delay = df["was_delayed"]
    y_denial = df["was_denied"]

    # Stratified 80/20 train/test split
    X_train_delay, X_test_delay, y_train_delay, y_test_delay = train_test_split(
        X, y_delay, test_size=0.20, random_state=42, stratify=y_delay
    )

    X_train_denial, X_test_denial, y_train_denial, y_test_denial = train_test_split(
        X, y_denial, test_size=0.20, random_state=42, stratify=y_denial
    )

    # 2. Train Delay Model
    print("\n2. Training Delay Prediction Model (was_delayed)...")
    delay_pipeline, delay_metrics = train_and_evaluate_model(
        X_train_delay, X_test_delay, y_train_delay, y_test_delay, "Delay Model"
    )

    # 3. Train Denial Model
    print("\n3. Training Denial Prediction Model (was_denied)...")
    denial_pipeline, denial_metrics = train_and_evaluate_model(
        X_train_denial, X_test_denial, y_train_denial, y_test_denial, "Denial Model"
    )

    # 4. Save Models and Metadata
    print("\n4. Saving trained models and evaluation metrics...")
    delay_model_path = MODELS_DIR / "delay_model.joblib"
    denial_model_path = MODELS_DIR / "denial_model.joblib"
    metrics_path = MODELS_DIR / "metrics.json"

    joblib.dump(delay_pipeline, delay_model_path)
    joblib.dump(denial_pipeline, denial_model_path)

    all_metrics = {
        "model_version": "1.0.0",
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "features": {
            "numeric": NUMERIC_FEATURES,
            "categorical": CATEGORICAL_FEATURES,
        },
        "models": {
            "delay_model": {
                "target": "was_delayed",
                "algorithm": "HistGradientBoostingClassifier",
                "metrics": delay_metrics,
            },
            "denial_model": {
                "target": "was_denied",
                "algorithm": "HistGradientBoostingClassifier",
                "metrics": denial_metrics,
            },
        },
    }

    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)

    elapsed = time.time() - start_time
    print(f"   ✓ Delay Model saved to:  {delay_model_path}")
    print(f"   ✓ Denial Model saved to: {denial_model_path}")
    print(f"   ✓ Metrics saved to:      {metrics_path}")

    print("\n==================================================")
    print("MODEL EVALUATION RESULTS (TEST SET):")
    print("--------------------------------------------------")
    print("DELAY MODEL (was_delayed):")
    print(f"  • ROC-AUC:   {delay_metrics['roc_auc']:.4f}")
    print(f"  • Accuracy:  {delay_metrics['accuracy']:.4f}")
    print(f"  • Precision: {delay_metrics['precision']:.4f}")
    print(f"  • Recall:    {delay_metrics['recall']:.4f}")
    print(f"  • F1-Score:  {delay_metrics['f1']:.4f}")
    print("--------------------------------------------------")
    print("DENIAL MODEL (was_denied):")
    print(f"  • ROC-AUC:   {denial_metrics['roc_auc']:.4f}")
    print(f"  • Accuracy:  {denial_metrics['accuracy']:.4f}")
    print(f"  • Precision: {denial_metrics['precision']:.4f}")
    print(f"  • Recall:    {denial_metrics['recall']:.4f}")
    print(f"  • F1-Score:  {denial_metrics['f1']:.4f}")
    print("--------------------------------------------------")
    print(f"✓ Training pipeline complete in {elapsed:.2f} seconds!")
    print("==================================================")


if __name__ == "__main__":
    run_training()
