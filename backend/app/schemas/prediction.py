from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class ModelMetricDetail(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    test_samples: int
    train_samples: int


class ModelInfo(BaseModel):
    target: str
    algorithm: str
    metrics: ModelMetricDetail


class MLMetricsResponse(BaseModel):
    model_version: str
    trained_at: str
    models: Dict[str, ModelInfo]


class PredictionResponse(BaseModel):
    claim_id: Optional[str] = None
    delay_probability: float
    denial_probability: float
    recovery_probability: float
    expected_recovery: float
    priority_score: Optional[float] = None
    priority_band: Optional[str] = None
    explainability_reasons: Optional[List[str]] = None
    model_version: str


class BatchPredictionRequest(BaseModel):
    claim_ids: List[str]


class PrioritizedClaimItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    claim_id: str
    patient_id: str
    provider_id: str
    payer_id: str
    payer_name: Optional[str] = None
    claim_date: str
    claim_type: str
    billed_amount: float
    outstanding_amount: float
    claim_status: str
    denial_reason: Optional[str] = None
    days_in_ar: int
    followup_count: int
    delay_probability: float
    denial_probability: float
    recovery_probability: float
    expected_recovery: float
    priority_score: float
    priority_band: str
    explainability_reasons: List[str] = []
