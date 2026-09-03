from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AgentDecisionSchema(BaseModel):
    claim_id: str
    recommended_action: str
    channel: str
    urgency: str
    confidence: float
    reasoning: str
    retrieved_policy_title: str
    retrieved_policy_snippet: str
    generated_message: str
    filing_deadline_remaining_days: int
    created_at: datetime


class ExecuteAgentActionRequest(BaseModel):
    simulate: bool = True
    custom_message: Optional[str] = None
    override_channel: Optional[str] = None


class AgentActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_id: int
    claim_id: str
    recommended_action: str
    reasoning: str
    confidence: Optional[float] = None
    retrieved_policy: Optional[str] = None
    generated_message: Optional[str] = None
    approval_status: str
    created_at: datetime
