from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.dashboard import (
    DashboardMetricsSchema,
    AgingBucketSchema,
    PayerPerformanceSchema,
    DenialReasonSchema,
    PriorityDistributionSchema,
)
from backend.app.services.dashboard_service import (
    get_dashboard_metrics,
    get_ar_aging_buckets,
    get_payer_performance,
    get_denial_reasons_breakdown,
    get_priority_distribution,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=DashboardMetricsSchema)
def get_metrics(db: Session = Depends(get_db)):
    """
    Retrieve real-time portfolio KPI metrics (Total AR, Critical Claims, Expected Recovery, Avg AR Age, Denial Rate).
    """
    return get_dashboard_metrics(db)


@router.get("/aging", response_model=List[AgingBucketSchema])
def get_aging_buckets(db: Session = Depends(get_db)):
    """
    Retrieve AR aging breakdown across standard intervals (0-30, 31-60, 61-90, 91-120, 120+).
    """
    return get_ar_aging_buckets(db)


@router.get("/payer-performance", response_model=List[PayerPerformanceSchema])
def get_payers_performance(db: Session = Depends(get_db)):
    """
    Retrieve payer volume, financial exposure, expected recoveries, and denial metrics.
    """
    return get_payer_performance(db)


@router.get("/denial-reasons", response_model=List[DenialReasonSchema])
def get_denial_reasons(db: Session = Depends(get_db)):
    """
    Retrieve top denial reasons breakdown with claim count and dollar impact.
    """
    return get_denial_reasons_breakdown(db)


@router.get("/priority-distribution", response_model=List[PriorityDistributionSchema])
def get_priority_bands(db: Session = Depends(get_db)):
    """
    Retrieve distribution of claims across Critical, High, Medium, and Low priority bands.
    """
    return get_priority_distribution(db)
