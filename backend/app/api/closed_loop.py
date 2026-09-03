from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database.session import get_db
from backend.app.models import Claim, ClaimOutcome, AgentAction
from backend.app.closed_loop.engine import closed_loop_engine
from backend.app.schemas.closed_loop import (
    RunClosedLoopRequest,
    ClosedLoopRunResponse,
    ClaimLoopExecutionSummary,
)

router = APIRouter(prefix="/closed-loop", tags=["Closed Loop Autonomous Recovery Engine"])


@router.post("/run", response_model=ClosedLoopRunResponse)
def run_closed_loop_recovery(
    payload: RunClosedLoopRequest,
    db: Session = Depends(get_db),
):
    """
    Execute autonomous end-to-end recovery cycle for a batch of high-priority claims:
    1. Select top prioritized claims
    2. Formulate AI strategy & retrieve RAG policy
    3. Generate custom communication artifacts
    4. Simulate payer adjudication response
    5. Update SQLite claim balances, state, and followup logs
    6. Record recovery yield and recompute metrics
    """
    result = closed_loop_engine.run_autonomous_loop(
        db=db,
        batch_size=payload.batch_size or 10,
        min_priority_band=payload.min_priority_band or "High",
        payer_id=payload.payer_id,
        action_quality=payload.action_quality or "high",
    )

    return ClosedLoopRunResponse(
        run_id=result["run_id"],
        timestamp=result["timestamp"],
        batch_size=result["batch_size"],
        total_processed=result["total_processed"],
        total_original_outstanding=result["total_original_outstanding"],
        total_recovered=result["total_recovered"],
        recovery_yield_percentage=result["recovery_yield_percentage"],
        outcomes_breakdown=result["outcomes_breakdown"],
        actions_breakdown=result["actions_breakdown"],
        updated_dashboard_total_ar=result["updated_dashboard_total_ar"],
        updated_dashboard_recovered_revenue=result["updated_dashboard_recovered_revenue"],
        results=[ClaimLoopExecutionSummary(**r) for r in result["results"]],
    )


@router.get("/summary")
def get_closed_loop_summary(
    db: Session = Depends(get_db),
):
    """
    Get live portfolio summary of all closed-loop actions and recovery metrics.
    """
    total_actions = db.query(func.count(AgentAction.action_id)).scalar() or 0
    total_recovered = db.query(func.sum(ClaimOutcome.recovered_amount)).scalar() or 0.0
    total_ar = db.query(func.sum(Claim.outstanding_amount)).scalar() or 0.0
    paid_claims_count = db.query(func.count(Claim.claim_id)).filter(Claim.claim_status == "Paid").scalar() or 0

    return {
        "total_actions_executed": total_actions,
        "total_recovered_revenue": round(float(total_recovered), 2),
        "current_outstanding_ar": round(float(total_ar), 2),
        "total_paid_claims": paid_claims_count,
    }
