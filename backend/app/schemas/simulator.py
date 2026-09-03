from typing import Optional, Dict, Any, List
from datetime import date
from pydantic import BaseModel


class SimulateResponseRequest(BaseModel):
    claim_id: str
    action_type: Optional[str] = "Appeal"  # 'Appeal', 'Status Inquiry', 'Resubmission', 'Escalation'
    channel: Optional[str] = "Portal"
    action_quality: Optional[str] = "high"  # 'high', 'standard', 'low'
    apply_to_db: Optional[bool] = False  # If true, updates claim status and creates followup outcome


class OutcomeProbabilityDistribution(BaseModel):
    p_approved_full: float
    p_approved_partial: float
    p_additional_info_required: float
    p_denial_upheld: float


class SimulationResultResponse(BaseModel):
    claim_id: str
    payer_id: str
    payer_name: str
    action_type: str
    channel: str
    simulated_outcome: str  # 'APPROVED_FULL', 'APPROVED_PARTIAL', 'ADDITIONAL_INFO_REQUIRED', 'DENIAL_UPHELD'
    recovered_amount: float
    original_outstanding: float
    remaining_outstanding: float
    new_claim_status: str
    turnaround_days: int
    simulated_response_date: str
    payer_response_text: str
    remittance_reference: str
    probability_distribution: OutcomeProbabilityDistribution
    applied_to_db: bool


class BatchSimulationRequest(BaseModel):
    claim_ids: List[str]
    action_type: Optional[str] = "Appeal"
    apply_to_db: Optional[bool] = False


class BatchSimulationResponse(BaseModel):
    total_simulated: int
    total_recovered: float
    outcomes_breakdown: Dict[str, int]
    results: List[SimulationResultResponse]
