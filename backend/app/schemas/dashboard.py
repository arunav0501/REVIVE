from typing import List, Optional
from pydantic import BaseModel


class DashboardMetricsSchema(BaseModel):
    total_ar: float
    total_claims: int
    critical_claims: int
    high_priority_claims: int
    expected_recovery: float
    recovered_revenue: float
    avg_days_in_ar: float
    denial_rate: float


class AgingBucketSchema(BaseModel):
    bucket: str
    min_days: int
    max_days: Optional[int] = None
    count: int
    total_outstanding: float
    expected_recovery: float


class PayerPerformanceSchema(BaseModel):
    payer_id: str
    payer_name: str
    plan_type: str
    total_claims: int
    total_outstanding: float
    expected_recovery: float
    avg_processing_days: int
    avg_response_days: int
    filing_deadline_days: int
    denial_rate: float


class DenialReasonSchema(BaseModel):
    reason: str
    count: int
    total_outstanding: float
    percentage: float


class PriorityDistributionSchema(BaseModel):
    band: str
    count: int
    total_outstanding: float
    expected_recovery: float
    percentage: float
