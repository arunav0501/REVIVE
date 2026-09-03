from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class RecommendedActionSchema(BaseModel):
    action_type: str
    channel: str
    urgency: str
    title: str
    description: str
    rationale: str


class PayerSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payer_id: str
    payer_name: str
    plan_type: str
    avg_processing_days: int
    avg_response_days: int
    filing_deadline_days: int
    preferred_contact_method: str


class FollowupItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    followup_id: str
    claim_id: str
    followup_date: str
    channel: str
    action_type: str
    message: str
    payer_response: Optional[str] = None
    response_date: Optional[str] = None
    outcome: Optional[str] = None


class ClaimOutcomeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: str
    final_outcome: str
    days_to_resolution: int
    was_denied: int
    was_delayed: int
    recovered_amount: float
    successful_followup: int


class PredictionSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prediction_id: int
    claim_id: str
    denial_probability: float
    delay_probability: float
    recovery_probability: float
    expected_recovery: float
    priority_score: float
    priority_band: str
    model_version: str


class ClaimListItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: str
    patient_id: str
    provider_id: str
    payer_id: str
    payer_name: Optional[str] = None
    claim_date: str
    service_date: str
    claim_type: str
    place_of_service: str
    billed_amount: float
    allowed_amount: float
    paid_amount: float
    patient_responsibility: float
    outstanding_amount: float
    expected_reimbursement: float
    claim_status: str
    denial_status: Optional[str] = None
    denial_code: Optional[str] = None
    denial_reason: Optional[str] = None
    days_in_ar: int
    followup_count: int
    resubmission_count: int
    appeal_status: str
    authorization_required: bool
    authorization_status: str
    network_status: str
    last_followup_date: Optional[str] = None
    last_payer_response: Optional[str] = None
    days_since_last_response: Optional[int] = None
    
    # ML Prioritization attributes
    delay_probability: Optional[float] = None
    denial_probability: Optional[float] = None
    recovery_probability: Optional[float] = None
    expected_recovery: Optional[float] = None
    priority_score: Optional[float] = None
    priority_band: Optional[str] = None
    explainability_reasons: Optional[List[str]] = None
    recommended_action: Optional[RecommendedActionSchema] = None


class ClaimDetailSchema(ClaimListItemSchema):
    filing_deadline_remaining_days: Optional[int] = None
    payer: Optional[PayerSummarySchema] = None
    followups: List[FollowupItemSchema] = []
    outcome: Optional[ClaimOutcomeSchema] = None
    prediction: Optional[PredictionSummarySchema] = None


class PaginatedClaimsResponse(BaseModel):
    items: List[ClaimListItemSchema]
    total: int
    page: int
    page_size: int
    total_pages: int
