from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.claim import (
    ClaimListItemSchema,
    ClaimDetailSchema,
    PaginatedClaimsResponse,
)
from backend.app.services.claim_service import (
    get_claims_list,
    get_claim_by_id,
    get_priority_claims,
)

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.get("", response_model=PaginatedClaimsResponse)
def list_claims(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(None, description="Search claim ID, patient, provider, or denial reason"),
    payer_id: Optional[str] = Query(None, description="Filter by Payer ID (e.g. PAY001)"),
    claim_status: Optional[str] = Query(None, description="Filter by Claim Status (e.g. Pending, Denied, Paid)"),
    denial_status: Optional[str] = Query(None, description="Filter by Denial Status"),
    claim_type: Optional[str] = Query(None, description="Filter by Claim Type (Inpatient, Outpatient, etc.)"),
    priority_band: Optional[str] = Query(None, description="Filter by Priority Band (Critical, High, Medium, Low)"),
    min_outstanding: Optional[float] = Query(None, ge=0, description="Minimum outstanding dollar amount"),
    max_outstanding: Optional[float] = Query(None, ge=0, description="Maximum outstanding dollar amount"),
    min_days_ar: Optional[int] = Query(None, ge=0, description="Minimum days in AR"),
    max_days_ar: Optional[int] = Query(None, ge=0, description="Maximum days in AR"),
    sort_by: str = Query("priority_score", description="Sort field (priority_score, days_in_ar, outstanding_amount, billed_amount, claim_date)"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction (asc or desc)"),
    db: Session = Depends(get_db),
):
    """
    Retrieve paginated claims with ML priority scores, multi-field filtering, sorting, and full-text search.
    """
    items, total, total_pages = get_claims_list(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        payer_id=payer_id,
        claim_status=claim_status,
        denial_status=denial_status,
        claim_type=claim_type,
        priority_band=priority_band,
        min_outstanding=min_outstanding,
        max_outstanding=max_outstanding,
        min_days_ar=min_days_ar,
        max_days_ar=max_days_ar,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return PaginatedClaimsResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/priority", response_model=List[ClaimListItemSchema])
def list_priority_claims(
    limit: int = Query(50, ge=1, le=100, description="Maximum priority claims to return"),
    payer_id: Optional[str] = Query(None, description="Filter by Payer ID"),
    priority_band: Optional[str] = Query(None, description="Filter by Priority Band (e.g. Critical, High)"),
    db: Session = Depends(get_db),
):
    """
    Retrieve claims prioritized by ML priority score (0-100), recovery potential, and explainable urgency.
    """
    return get_priority_claims(db=db, limit=limit, payer_id=payer_id, priority_band=priority_band)


@router.get("/{claim_id}", response_model=ClaimDetailSchema)
def get_single_claim(
    claim_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve single claim details with connected ML priority analysis, explainability factors, payer policy, and followups.
    """
    result = get_claim_by_id(db=db, claim_id=claim_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' not found",
        )

    claim = result["claim"]
    return ClaimDetailSchema(
        claim_id=claim.claim_id,
        patient_id=claim.patient_id,
        provider_id=claim.provider_id,
        payer_id=claim.payer_id,
        payer_name=claim.payer.payer_name if claim.payer else None,
        claim_date=claim.claim_date,
        service_date=claim.service_date,
        claim_type=claim.claim_type,
        place_of_service=claim.place_of_service,
        billed_amount=claim.billed_amount,
        allowed_amount=claim.allowed_amount,
        paid_amount=claim.paid_amount,
        patient_responsibility=claim.patient_responsibility,
        outstanding_amount=claim.outstanding_amount,
        expected_reimbursement=claim.expected_reimbursement,
        claim_status=claim.claim_status,
        denial_status=claim.denial_status,
        denial_code=claim.denial_code,
        denial_reason=claim.denial_reason,
        days_in_ar=claim.days_in_ar,
        followup_count=claim.followup_count,
        resubmission_count=claim.resubmission_count,
        appeal_status=claim.appeal_status,
        authorization_required=claim.authorization_required,
        authorization_status=claim.authorization_status,
        network_status=claim.network_status,
        last_followup_date=claim.last_followup_date,
        last_payer_response=claim.last_payer_response,
        days_since_last_response=claim.days_since_last_response,
        delay_probability=result["delay_probability"],
        denial_probability=result["denial_probability"],
        recovery_probability=result["recovery_probability"],
        expected_recovery=result["expected_recovery"],
        priority_score=result["priority_score"],
        priority_band=result["priority_band"],
        explainability_reasons=result["explainability_reasons"],
        recommended_action=result["recommended_action"],
        filing_deadline_remaining_days=result["filing_deadline_remaining_days"],
        payer=claim.payer,
        followups=claim.followups,
        outcome=claim.outcome,
        prediction=claim.prediction,
    )

