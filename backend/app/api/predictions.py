from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Claim, Payer
from backend.app.ml import predictor
from backend.app.schemas.prediction import (
    MLMetricsResponse,
    PredictionResponse,
    BatchPredictionRequest,
)

router = APIRouter(prefix="/predictions", tags=["Predictions"])


def _claim_to_feature_dict(claim: Claim) -> dict:
    """Helper to convert Claim ORM object to feature dictionary with joined payer values."""
    payer = claim.payer
    return {
        "claim_id": claim.claim_id,
        "days_in_ar": claim.days_in_ar,
        "outstanding_amount": claim.outstanding_amount,
        "billed_amount": claim.billed_amount,
        "allowed_amount": claim.allowed_amount,
        "paid_amount": claim.paid_amount,
        "patient_responsibility": claim.patient_responsibility,
        "expected_reimbursement": claim.expected_reimbursement,
        "followup_count": claim.followup_count,
        "resubmission_count": claim.resubmission_count,
        "days_since_last_response": claim.days_since_last_response,
        "avg_processing_days": payer.avg_processing_days if payer else 15,
        "avg_response_days": payer.avg_response_days if payer else 7,
        "filing_deadline_days": payer.filing_deadline_days if payer else 90,
        "payer_id": claim.payer_id,
        "claim_type": claim.claim_type,
        "place_of_service": claim.place_of_service,
        "claim_status": claim.claim_status,
        "denial_status": claim.denial_status,
        "denial_code": claim.denial_code,
        "denial_reason": claim.denial_reason,
        "authorization_required": str(claim.authorization_required),
        "authorization_status": claim.authorization_status,
        "network_status": claim.network_status,
        "appeal_status": claim.appeal_status,
    }


@router.get("/metrics", response_model=MLMetricsResponse)
def get_model_metrics():
    """
    Retrieve real evaluation metrics calculated from the test set for both trained models.
    """
    metrics = predictor.get_metrics()
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trained model metrics not found. Run scripts/train_models.py first.",
        )
    return metrics


@router.post("/batch", response_model=List[PredictionResponse])
def predict_batch_claims(payload: BatchPredictionRequest, db: Session = Depends(get_db)):
    """
    Execute batch ML inference for a list of claim IDs.
    """
    claims = db.query(Claim).filter(Claim.claim_id.in_(payload.claim_ids)).all()
    if not claims:
        return []

    feature_dicts = [_claim_to_feature_dict(c) for c in claims]
    results = predictor.predict_batch(feature_dicts)
    return [PredictionResponse(**r) for r in results]


@router.post("/{claim_id}", response_model=PredictionResponse)
def predict_single_claim(claim_id: str, db: Session = Depends(get_db)):
    """
    Execute real-time ML model inference for a specific claim.
    Returns predicted delay probability, denial probability, recovery probability, and expected dollar recovery.
    """
    claim = db.query(Claim).filter(Claim.claim_id == claim_id.strip()).first()
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' not found",
        )

    feature_dict = _claim_to_feature_dict(claim)
    result = predictor.predict_claim(feature_dict)
    return PredictionResponse(**result)

