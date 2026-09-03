from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class GenerateArtifactRequest(BaseModel):
    claim_id: str
    artifact_type: Optional[str] = "all"  # 'all', 'appeal_letter', 'portal_message', 'phone_script', 'email_template'
    tone: Optional[str] = "firm"  # 'firm', 'urgent', 'collaborative'
    custom_notes: Optional[str] = None


class GeneratedArtifactsResponse(BaseModel):
    claim_id: str
    patient_id: str
    provider_id: str
    payer_name: str
    payer_id: str
    denial_code: Optional[str] = None
    denial_reason: Optional[str] = None
    outstanding_amount: float
    grounded_policy_title: str
    grounded_policy_content: str
    appeal_letter: Optional[str] = None
    portal_message: Optional[str] = None
    phone_script: Optional[str] = None
    email_template: Optional[str] = None
    edi_resubmission_note: Optional[str] = None


class TemplateScenarioInfo(BaseModel):
    scenario_name: str
    denial_code: str
    description: str
    recommended_artifacts: List[str]


class TemplateCatalogResponse(BaseModel):
    available_artifact_types: List[str]
    scenarios: List[TemplateScenarioInfo]
