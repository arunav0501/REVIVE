from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel


class RunClosedLoopRequest(BaseModel):
    batch_size: Optional[int] = 10  # 1 to 50 claims
    min_priority_band: Optional[str] = "High"  # 'Critical', 'High', 'Medium', 'All'
    payer_id: Optional[str] = None
    action_quality: Optional[str] = "high"


class ClaimLoopExecutionSummary(BaseModel):
    claim_id: str
    patient_id: str
    payer_id: str
    payer_name: str
    priority_score: float
    priority_band: str
    initial_status: str
    chosen_action: str
    chosen_channel: str
    grounded_policy_title: str
    simulated_outcome: str
    original_outstanding: float
    recovered_amount: float
    final_outstanding: float
    final_status: str
    payer_response_snippet: str
    remittance_reference: str


class ClosedLoopRunResponse(BaseModel):
    run_id: str
    timestamp: str
    batch_size: int
    total_processed: int
    total_original_outstanding: float
    total_recovered: float
    recovery_yield_percentage: float
    outcomes_breakdown: Dict[str, int]
    actions_breakdown: Dict[str, int]
    updated_dashboard_total_ar: float
    updated_dashboard_recovered_revenue: float
    results: List[ClaimLoopExecutionSummary]
