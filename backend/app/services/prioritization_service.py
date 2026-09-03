"""
AR Follow-Up AI - Prioritization & Explainability Engine (Phase 5)

Calculates:
1. Expected Financial Recovery: outstanding_amount * recovery_probability
2. Priority Score: 0.45 * recovery_probability + 0.30 * delay_probability + 0.25 * normalized_outstanding (0-100)
3. Priority Bands: Low (0-40), Medium (40-70), High (70-85), Critical (85-100)
4. Deterministic Explainability Factors derived from actual claim data, payer behaviors, and ML predictions.
5. Populates & manages SQLite predictions table.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import numpy as np
from sqlalchemy.orm import Session

from backend.app.models import Claim, Payer, Prediction
from backend.app.ml import predictor

# Default configurable weights
DEFAULT_WEIGHT_RECOVERY = 0.45
DEFAULT_WEIGHT_DELAY = 0.30
DEFAULT_WEIGHT_AMOUNT = 0.25
MAX_OUTSTANDING_SCALE = 50000.0  # Scale ceiling for normalization


def calculate_priority(
    outstanding_amount: float,
    recovery_probability: float,
    delay_probability: float,
    w_recovery: float = DEFAULT_WEIGHT_RECOVERY,
    w_delay: float = DEFAULT_WEIGHT_DELAY,
    w_amount: float = DEFAULT_WEIGHT_AMOUNT,
) -> tuple[float, str, float]:
    """
    Computes expected_recovery, priority_score (0-100), and priority_band.
    """
    expected_recovery = round(float(outstanding_amount * recovery_probability), 2)

    # Normalize outstanding amount between 0.0 and 1.0 with a soft curve
    norm_amount = min(1.0, max(0.0, float(outstanding_amount) / MAX_OUTSTANDING_SCALE))

    # Calculate weighted priority score
    raw_score = (
        (w_recovery * recovery_probability) +
        (w_delay * delay_probability) +
        (w_amount * norm_amount)
    )

    priority_score = round(float(np.clip(raw_score * 100.0, 0.0, 100.0)), 1)

    # Assign priority band according to spec
    if priority_score >= 85.0:
        priority_band = "Critical"
    elif priority_score >= 70.0:
        priority_band = "High"
    elif priority_score >= 40.0:
        priority_band = "Medium"
    else:
        priority_band = "Low"

    return priority_score, priority_band, expected_recovery


def generate_explainability_factors(
    claim_dict: Dict[str, Any],
    delay_prob: float,
    denial_prob: float,
    recovery_prob: float,
    expected_recovery: float,
    priority_score: float,
    priority_band: str,
) -> List[str]:
    """
    Generates explainable, deterministic reasons derived directly from claim attributes and ML outputs.
    """
    reasons = []

    outstanding = float(claim_dict.get("outstanding_amount", 0.0))
    days_ar = int(claim_dict.get("days_in_ar", 0))
    followups = int(claim_dict.get("followup_count", 0))
    denial_reason = claim_dict.get("denial_reason")
    denial_code = claim_dict.get("denial_code")
    payer_name = claim_dict.get("payer_name") or claim_dict.get("payer_id") or "Payer"
    filing_deadline = claim_dict.get("filing_deadline_days")
    avg_resp = claim_dict.get("avg_response_days")
    auth_status = claim_dict.get("authorization_status")

    # Financial factor
    if outstanding >= 15000:
        reasons.append(f"${outstanding:,.2f} significant outstanding balance requiring immediate attention")
    elif outstanding > 0:
        reasons.append(f"${outstanding:,.2f} outstanding claim balance (${expected_recovery:,.2f} expected recovery)")

    # AR Aging factor
    if filing_deadline and (filing_deadline - days_ar <= 30) and (filing_deadline - days_ar > 0):
        reasons.append(f"{days_ar} days in AR — approaching {payer_name}'s {filing_deadline}-day filing deadline ({filing_deadline - days_ar} days remaining)")
    elif days_ar >= 90:
        reasons.append(f"Severely aged in AR ({days_ar} days) beyond standard 90-day cycle")
    elif days_ar >= 45:
        reasons.append(f"{days_ar} days in AR exceeding normal 30-day reimbursement threshold")

    # Delay Risk factor
    if delay_prob >= 0.75:
        reasons.append(f"{int(delay_prob * 100)}% high predicted delay risk from payer processing behavior")
    elif delay_prob >= 0.50:
        reasons.append(f"{int(delay_prob * 100)}% moderate predicted processing delay")

    # Denial Risk factor
    if denial_prob >= 0.70:
        reasons.append(f"{int(denial_prob * 100)}% critical denial probability based on claim clinical profile")
    elif denial_prob >= 0.40:
        reasons.append(f"{int(denial_prob * 100)}% elevated denial risk")

    # Denial Reason factor
    if denial_reason:
        code_str = f" ({denial_code})" if denial_code else ""
        reasons.append(f"Recorded denial: '{denial_reason}'{code_str}")

    # Follow-up history factor
    if followups >= 3:
        reasons.append(f"{followups} previous follow-up attempts with no final resolution")
    elif followups > 0:
        reasons.append(f"{followups} previous follow-up logged")

    # Payer latency factor
    if avg_resp and avg_resp >= 7:
        reasons.append(f"{payer_name} historically exhibits slow response turnaround (~{avg_resp} days)")

    # Authorization factor
    if auth_status and auth_status not in ["Not Required", "Approved"]:
        reasons.append(f"Prior authorization issue: status is '{auth_status}'")

    # High recovery potential
    if recovery_prob >= 0.70 and outstanding >= 5000:
        reasons.append(f"Strong recovery viability ({int(recovery_prob * 100)}% probability of recovering funds)")

    return reasons[:6]


def evaluate_and_score_claim(claim_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs ML predictor, calculates expected recovery and priority score, and generates explainability reasons.
    """
    pred = predictor.predict_claim(claim_dict)
    delay_p = pred["delay_probability"]
    denial_p = pred["denial_probability"]
    recovery_p = pred["recovery_probability"]
    outstanding = float(claim_dict.get("outstanding_amount", 0.0))

    score, band, expected_rec = calculate_priority(
        outstanding_amount=outstanding,
        recovery_probability=recovery_p,
        delay_probability=delay_p,
    )

    reasons = generate_explainability_factors(
        claim_dict=claim_dict,
        delay_prob=delay_p,
        denial_prob=denial_p,
        recovery_prob=recovery_p,
        expected_recovery=expected_rec,
        priority_score=score,
        priority_band=band,
    )

    return {
        "claim_id": claim_dict.get("claim_id"),
        "denial_probability": denial_p,
        "delay_probability": delay_p,
        "recovery_probability": recovery_p,
        "expected_recovery": expected_rec,
        "priority_score": score,
        "priority_band": band,
        "explainability_reasons": reasons,
        "model_version": pred.get("model_version", "1.0.0"),
    }


def populate_all_predictions(db: Session, batch_size: int = 1000) -> int:
    """
    Scores all claims in SQLite and populates/updates the predictions table.
    """
    claims = db.query(Claim).all()
    if not claims:
        return 0

    # Clear existing predictions to avoid duplicates
    db.query(Prediction).delete()
    db.commit()

    feature_dicts = []
    for c in claims:
        p = c.payer
        feature_dicts.append({
            "claim_id": c.claim_id,
            "days_in_ar": c.days_in_ar,
            "outstanding_amount": c.outstanding_amount,
            "billed_amount": c.billed_amount,
            "allowed_amount": c.allowed_amount,
            "paid_amount": c.paid_amount,
            "patient_responsibility": c.patient_responsibility,
            "expected_reimbursement": c.expected_reimbursement,
            "followup_count": c.followup_count,
            "resubmission_count": c.resubmission_count,
            "days_since_last_response": c.days_since_last_response,
            "avg_processing_days": p.avg_processing_days if p else 15,
            "avg_response_days": p.avg_response_days if p else 7,
            "filing_deadline_days": p.filing_deadline_days if p else 90,
            "payer_id": c.payer_id,
            "payer_name": p.payer_name if p else None,
            "claim_type": c.claim_type,
            "place_of_service": c.place_of_service,
            "claim_status": c.claim_status,
            "denial_status": c.denial_status,
            "denial_code": c.denial_code,
            "denial_reason": c.denial_reason,
            "authorization_required": str(c.authorization_required),
            "authorization_status": c.authorization_status,
            "network_status": c.network_status,
            "appeal_status": c.appeal_status,
        })

    # Batch ML inference
    ml_results = predictor.predict_batch(feature_dicts)

    prediction_records = []
    now = datetime.now(timezone.utc)

    for i, c_dict in enumerate(feature_dicts):
        ml_res = ml_results[i]
        delay_p = ml_res["delay_probability"]
        denial_p = ml_res["denial_probability"]
        recovery_p = ml_res["recovery_probability"]
        outstanding = float(c_dict["outstanding_amount"])

        score, band, exp_rec = calculate_priority(
            outstanding_amount=outstanding,
            recovery_probability=recovery_p,
            delay_probability=delay_p,
        )

        pred_obj = Prediction(
            claim_id=c_dict["claim_id"],
            denial_probability=denial_p,
            delay_probability=delay_p,
            recovery_probability=recovery_p,
            expected_recovery=exp_rec,
            priority_score=score,
            priority_band=band,
            model_version=ml_res.get("model_version", "1.0.0"),
            created_at=now,
        )
        prediction_records.append(pred_obj)

        if len(prediction_records) >= batch_size:
            db.bulk_save_objects(prediction_records)
            db.commit()
            prediction_records = []

    if prediction_records:
        db.bulk_save_objects(prediction_records)
        db.commit()

    return len(claims)
