from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Claim
from backend.app.simulator.payer_simulator import payer_simulator
from backend.app.schemas.simulator import (
    SimulateResponseRequest,
    SimulationResultResponse,
    BatchSimulationRequest,
    BatchSimulationResponse,
    OutcomeProbabilityDistribution,
)

router = APIRouter(prefix="/simulator", tags=["Payer Response Simulator"])


@router.post("/simulate", response_model=SimulationResultResponse)
def simulate_payer_response(
    payload: SimulateResponseRequest,
    db: Session = Depends(get_db),
):
    """
    Simulate realistic payer response outcome (Approved Full, Approved Partial,
    Additional Info Required, Denial Upheld) based on claim state and action quality.
    """
    claim = db.query(Claim).filter(Claim.claim_id == payload.claim_id.strip()).first()
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{payload.claim_id}' not found",
        )

    result = payer_simulator.simulate_response(
        claim=claim,
        action_type=payload.action_type or "Appeal",
        channel=payload.channel or "Portal",
        action_quality=payload.action_quality or "high",
        apply_to_db=payload.apply_to_db or False,
        db=db,
    )
    return SimulationResultResponse(
        claim_id=result["claim_id"],
        payer_id=result["payer_id"],
        payer_name=result["payer_name"],
        action_type=result["action_type"],
        channel=result["channel"],
        simulated_outcome=result["simulated_outcome"],
        recovered_amount=result["recovered_amount"],
        original_outstanding=result["original_outstanding"],
        remaining_outstanding=result["remaining_outstanding"],
        new_claim_status=result["new_claim_status"],
        turnaround_days=result["turnaround_days"],
        simulated_response_date=result["simulated_response_date"],
        payer_response_text=result["payer_response_text"],
        remittance_reference=result["remittance_reference"],
        probability_distribution=OutcomeProbabilityDistribution(**result["probability_distribution"]),
        applied_to_db=result["applied_to_db"],
    )


@router.get("/probabilities/{claim_id}", response_model=OutcomeProbabilityDistribution)
def get_claim_outcome_probabilities(
    claim_id: str,
    action_type: str = Query("Appeal"),
    action_quality: str = Query("high"),
    db: Session = Depends(get_db),
):
    """
    Retrieve calculated 4-class probability distribution for a specific claim and action.
    """
    claim = db.query(Claim).filter(Claim.claim_id == claim_id.strip()).first()
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' not found",
        )

    probs = payer_simulator.calculate_probability_distribution(
        claim=claim,
        action_type=action_type,
        action_quality=action_quality,
    )
    return OutcomeProbabilityDistribution(**probs)


@router.post("/batch", response_model=BatchSimulationResponse)
def simulate_batch_responses(
    payload: BatchSimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Simulate batch payer responses across multiple claims.
    """
    results = []
    total_recovered = 0.0
    breakdown: Dict[str, int] = {
        "APPROVED_FULL": 0,
        "APPROVED_PARTIAL": 0,
        "ADDITIONAL_INFO_REQUIRED": 0,
        "DENIAL_UPHELD": 0,
    }

    for cid in payload.claim_ids[:50]:
        claim = db.query(Claim).filter(Claim.claim_id == cid.strip()).first()
        if not claim:
            continue

        res = payer_simulator.simulate_response(
            claim=claim,
            action_type=payload.action_type or "Appeal",
            apply_to_db=payload.apply_to_db or False,
            db=db,
        )
        total_recovered += res["recovered_amount"]
        breakdown[res["simulated_outcome"]] = breakdown.get(res["simulated_outcome"], 0) + 1

        results.append(
            SimulationResultResponse(
                claim_id=res["claim_id"],
                payer_id=res["payer_id"],
                payer_name=res["payer_name"],
                action_type=res["action_type"],
                channel=res["channel"],
                simulated_outcome=res["simulated_outcome"],
                recovered_amount=res["recovered_amount"],
                original_outstanding=res["original_outstanding"],
                remaining_outstanding=res["remaining_outstanding"],
                new_claim_status=res["new_claim_status"],
                turnaround_days=res["turnaround_days"],
                simulated_response_date=res["simulated_response_date"],
                payer_response_text=res["payer_response_text"],
                remittance_reference=res["remittance_reference"],
                probability_distribution=OutcomeProbabilityDistribution(**res["probability_distribution"]),
                applied_to_db=res["applied_to_db"],
            )
        )

    return BatchSimulationResponse(
        total_simulated=len(results),
        total_recovered=round(total_recovered, 2),
        outcomes_breakdown=breakdown,
        results=results,
    )
