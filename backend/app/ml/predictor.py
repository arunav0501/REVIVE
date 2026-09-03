"""
AR Follow-Up AI - ML Prediction Engine (Phase 4)

Loads trained Scikit-Learn pipelines and computes real-time predictions:
- delay_probability (P(was_delayed))
- denial_probability (P(was_denied))
- recovery_probability (Transparent formula combining risk factors and historical recoverability)
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import joblib
import pandas as pd
import numpy as np

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BACKEND_DIR / "trained_models"


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


class MLPredictor:
    def __init__(self):
        self.delay_model = None
        self.denial_model = None
        self.metrics = {}
        self.is_loaded = False
        self.load_models()

    def load_models(self):
        """Load trained model artifacts and metrics."""
        delay_path = MODELS_DIR / "delay_model.joblib"
        denial_path = MODELS_DIR / "denial_model.joblib"
        metrics_path = MODELS_DIR / "metrics.json"

        if delay_path.exists() and denial_path.exists():
            try:
                self.delay_model = joblib.load(delay_path)
                self.denial_model = joblib.load(denial_path)
                if metrics_path.exists():
                    with open(metrics_path, "r") as f:
                        self.metrics = json.load(f)
                self.is_loaded = True
            except Exception as e:
                print(f"[!] Warning: Failed to load models from {MODELS_DIR}: {e}")
                self.is_loaded = False

    def _prepare_df(self, claims: List[Dict[str, Any]]) -> pd.DataFrame:
        """Standardize input dicts into the required feature DataFrame."""
        rows = []
        for c in claims:
            row = {}
            for col in NUMERIC_FEATURES:
                val = c.get(col)
                row[col] = float(val) if val is not None else 0.0

            for col in CATEGORICAL_FEATURES:
                val = c.get(col)
                row[col] = str(val).strip() if val is not None else "Missing"

            rows.append(row)

        df = pd.DataFrame(rows)
        return df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]

    def calculate_recovery_probability(
        self,
        claim: Dict[str, Any],
        denial_prob: float,
        delay_prob: float,
    ) -> float:
        """
        Calculate transparent recovery probability based on denial risk, network status,
        authorization, and appeal status.
        Formula: Base recoverability (1.0 - 0.65 * denial_risk) adjusted by auth/network factors.
        """
        # Base recovery inversely correlated with denial probability
        base_recovery = max(0.05, 1.0 - (0.65 * denial_prob) - (0.15 * delay_prob))

        # Adjust for network status
        network = str(claim.get("network_status", "In-Network")).lower()
        if "out" in network:
            base_recovery *= 0.85

        # Adjust for authorization status
        auth_status = str(claim.get("authorization_status", "")).lower()
        if "denied" in auth_status:
            base_recovery *= 0.60
        elif "pending" in auth_status:
            base_recovery *= 0.88
        elif "approved" in auth_status:
            base_recovery = min(0.98, base_recovery * 1.08)

        # Adjust for appeal status
        appeal = str(claim.get("appeal_status", "")).lower()
        if "under review" in appeal or "in progress" in appeal:
            base_recovery = min(0.95, base_recovery * 1.05)

        # Aging decay factor for claims in AR over 90 days
        days_ar = float(claim.get("days_in_ar", 0))
        if days_ar > 120:
            base_recovery *= 0.82
        elif days_ar > 90:
            base_recovery *= 0.90

        return round(float(np.clip(base_recovery, 0.05, 0.98)), 4)

    def predict_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate full ML predictions for a single claim dictionary."""
        if not self.is_loaded:
            self.load_models()

        df = self._prepare_df([claim_data])

        if self.is_loaded and self.delay_model and self.denial_model:
            delay_prob = round(float(self.delay_model.predict_proba(df)[0, 1]), 4)
            denial_prob = round(float(self.denial_model.predict_proba(df)[0, 1]), 4)
        else:
            # Deterministic heuristic fallback if models are not loaded
            days_ar = float(claim_data.get("days_in_ar", 30))
            delay_prob = round(float(np.clip(days_ar / 120.0, 0.1, 0.95)), 4)
            denial_prob = 0.75 if claim_data.get("denial_status") == "Denied" else 0.20

        recovery_prob = self.calculate_recovery_probability(claim_data, denial_prob, delay_prob)

        outstanding = float(claim_data.get("outstanding_amount", 0.0))
        expected_recovery = round(outstanding * recovery_prob, 2)

        return {
            "claim_id": claim_data.get("claim_id"),
            "delay_probability": delay_prob,
            "denial_probability": denial_prob,
            "recovery_probability": recovery_prob,
            "expected_recovery": expected_recovery,
            "model_version": self.metrics.get("model_version", "1.0.0"),
        }

    def predict_batch(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate ML predictions for a batch of claims efficiently."""
        if not claims:
            return []

        if not self.is_loaded:
            self.load_models()

        df = self._prepare_df(claims)

        if self.is_loaded and self.delay_model and self.denial_model:
            delay_probs = self.delay_model.predict_proba(df)[:, 1]
            denial_probs = self.denial_model.predict_proba(df)[:, 1]
        else:
            delay_probs = np.array([0.5] * len(claims))
            denial_probs = np.array([0.25] * len(claims))

        results = []
        for i, claim in enumerate(claims):
            del_p = round(float(delay_probs[i]), 4)
            den_p = round(float(denial_probs[i]), 4)
            rec_p = self.calculate_recovery_probability(claim, den_p, del_p)
            outstanding = float(claim.get("outstanding_amount", 0.0))
            exp_rec = round(outstanding * rec_p, 2)

            results.append({
                "claim_id": claim.get("claim_id"),
                "delay_probability": del_p,
                "denial_probability": den_p,
                "recovery_probability": rec_p,
                "expected_recovery": exp_rec,
                "model_version": self.metrics.get("model_version", "1.0.0"),
            })

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """Return saved model evaluation metrics."""
        return self.metrics


# Global singleton instance
predictor = MLPredictor()
