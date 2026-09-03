from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.database.session import get_db
from backend.app.models import Claim, AgentAction
from backend.app.agent.followup_agent import followup_agent
from backend.app.schemas.agent import (
    AgentDecisionSchema,
    ExecuteAgentActionRequest,
    AgentActionResponse,
)

router = APIRouter(prefix="/agent", tags=["AI Follow-Up Agent"])


@router.post("/decide/{claim_id}", response_model=AgentDecisionSchema)
def formulate_agent_decision(claim_id: str, db: Session = Depends(get_db)):
    """
    Intake claim profile, retrieve RAG policy rules, determine optimal action/channel,
    and generate professional appeal letter or inquiry draft.
    """
    claim = db.query(Claim).filter(Claim.claim_id == claim_id.strip()).first()
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' not found",
        )

    decision = followup_agent.formulate_decision(claim)
    return AgentDecisionSchema(**decision)


@router.post("/execute/{claim_id}", response_model=AgentActionResponse)
def execute_agent_action(
    claim_id: str,
    payload: ExecuteAgentActionRequest = ExecuteAgentActionRequest(),
    db: Session = Depends(get_db),
):
    """
    Execute autonomous follow-up action (supports simulated execution),
    persisting the record in agent_actions and logging a new entry in followups.
    """
    try:
        result = followup_agent.execute_action(
            db=db,
            claim_id=claim_id,
            simulate=payload.simulate,
            custom_message=payload.custom_message,
            override_channel=payload.override_channel,
        )
        return AgentActionResponse(
            action_id=result["action_id"],
            claim_id=result["claim_id"],
            recommended_action=result["recommended_action"],
            reasoning=result["reasoning"],
            confidence=result["confidence"],
            retrieved_policy=None,
            generated_message=result["generated_message"],
            approval_status=result["approval_status"],
            created_at=result["created_at"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/actions", response_model=List[AgentActionResponse])
def list_agent_actions(
    limit: int = Query(50, ge=1, le=100),
    claim_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List historical autonomous agent actions and generated drafts.
    """
    query = db.query(AgentAction)
    if claim_id:
        query = query.filter(AgentAction.claim_id == claim_id.strip())
    
    actions = query.order_by(desc(AgentAction.created_at)).limit(limit).all()
    return [AgentActionResponse.model_validate(a) for a in actions]


@router.get("/actions/{claim_id}", response_model=List[AgentActionResponse])
def get_claim_agent_actions(claim_id: str, db: Session = Depends(get_db)):
    """
    Get all agent decisions and executions for a specific claim.
    """
    actions = (
        db.query(AgentAction)
        .filter(AgentAction.claim_id == claim_id.strip())
        .order_by(desc(AgentAction.created_at))
        .all()
    )
    return [AgentActionResponse.model_validate(a) for a in actions]
