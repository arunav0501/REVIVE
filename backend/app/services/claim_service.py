from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, asc

from backend.app.models import Claim, Payer, Followup, ClaimOutcome, Prediction
from backend.app.services.prioritization_service import (
    generate_explainability_factors,
    evaluate_and_score_claim,
)


ALLOWED_SORT_FIELDS = {
    "priority_score": Prediction.priority_score,
    "outstanding_amount": Claim.outstanding_amount,
    "days_in_ar": Claim.days_in_ar,
    "billed_amount": Claim.billed_amount,
    "claim_date": Claim.claim_date,
    "followup_count": Claim.followup_count,
    "claim_id": Claim.claim_id,
}


def generate_recommended_action(
    claim_status: str,
    denial_status: Optional[str],
    denial_reason: Optional[str],
    denial_code: Optional[str],
    days_in_ar: int,
    filing_deadline_days: int,
    priority_band: str,
    preferred_contact: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generates an intelligent, context-aware recommended next action tailored to the claim.
    """
    channel = preferred_contact or "Payer Portal"
    urgency = "Immediate" if priority_band == "Critical" else "High" if priority_band == "High" else "Standard"
    remaining_days = max(0, filing_deadline_days - days_in_ar)

    if denial_status == "Denied" or claim_status == "Denied":
        reason_lower = (denial_reason or "").lower()
        code_str = f" ({denial_code})" if denial_code else ""

        if "missing" in reason_lower or denial_code == "CO-16":
            return {
                "action_type": "Appeal",
                "channel": channel,
                "urgency": "Immediate" if remaining_days < 30 else urgency,
                "title": f"Submit Clinical Documentation Appeal{code_str}",
                "description": "Assemble missing itemized billing statements, medical charts, and doctor's operative notes and submit electronically via the payer provider portal.",
                "rationale": f"The claim was denied for missing information. Payer filing deadline allows {remaining_days} days to submit corrected documentation.",
            }
        elif "prior auth" in reason_lower or "authorization" in reason_lower or denial_code == "CO-197":
            return {
                "action_type": "Appeal",
                "channel": "Payer Portal / Fax",
                "urgency": "Immediate",
                "title": f"File Retroactive Prior Authorization Appeal{code_str}",
                "description": "Submit urgent retroactive authorization request with treating physician's clinical justification letter and medical records.",
                "rationale": "Service performed requires authorization review; submit retroactive medical necessity package before appeal window closes.",
            }
        elif "medical necessity" in reason_lower or denial_code == "CO-50":
            return {
                "action_type": "Appeal",
                "channel": "Phone / Medical Review Portal",
                "urgency": "High",
                "title": f"Request Clinical Peer-to-Peer Review{code_str}",
                "description": "Schedule a peer-to-peer case discussion between the provider and payer Medical Director, backed by clinical guidelines.",
                "rationale": "Medical necessity denials are most effectively overturned via direct clinician dialogue and supporting peer literature.",
            }
        elif "timely filing" in reason_lower or denial_code == "CO-29":
            return {
                "action_type": "Appeal",
                "channel": "Certified Mail / EDI",
                "urgency": "Immediate",
                "title": f"Submit Proof of Timely Filing Dispute{code_str}",
                "description": "Generate electronic EDI 999 / 277 clearinghouse acceptance receipts proving original submission was within the required deadline.",
                "rationale": "Clearinghouse batch transmission logs provide conclusive proof of timely initial filing.",
            }
        elif "duplicate" in reason_lower or denial_code == "CO-18":
            return {
                "action_type": "Resubmission",
                "channel": channel,
                "urgency": "Standard",
                "title": f"Reconcile EOB & Resubmit with Modifiers{code_str}",
                "description": "Review initial claim Remittance Advice, verify distinct service units, and resubmit with appropriate billing modifiers (e.g., -59 or -76).",
                "rationale": "Resolving duplicate line item flags requires distinct procedure modifier validation.",
            }
        else:
            return {
                "action_type": "Appeal",
                "channel": channel,
                "urgency": urgency,
                "title": f"Initiate Level-1 Claim Dispute{code_str}",
                "description": f"Draft and file a formal First-Level Administrative Appeal addressing denial root cause: '{denial_reason or 'Claim Disallowance'}'.",
                "rationale": "Formal written dispute is required to reopen adjudication on denied balances.",
            }

    elif claim_status == "Appeal Pending":
        return {
            "action_type": "Status Inquiry",
            "channel": "Phone Call / Portal",
            "urgency": "High" if days_in_ar > 60 else "Standard",
            "title": "Follow Up on Outstanding Appeal Determination",
            "description": "Contact payer appeals unit to verify receipt of appeal package and obtain the expected resolution date.",
            "rationale": "Appeal has been logged; confirm adjudicator assignment and eliminate processing bottlenecks.",
        }

    elif claim_status in ["Pending", "In Review"]:
        if days_in_ar > 45:
            return {
                "action_type": "Status Inquiry",
                "channel": channel,
                "urgency": "High",
                "title": "Issue Escalated Claim Status Inquiry",
                "description": "Submit automated EDI 276 / Portal claim status inquiry requesting immediate adjudication update on aging balance.",
                "rationale": f"Claim has been in AR for {days_in_ar} days, exceeding typical 30-day reimbursement turnaround.",
            }
        else:
            return {
                "action_type": "Status Inquiry",
                "channel": "Automated Portal Check",
                "urgency": "Standard",
                "title": "Monitor Standard Adjudication Cycle",
                "description": "Claim is currently within normal payer turnaround window. Maintain weekly automated electronic status check.",
                "rationale": "No active denial flagged; proceed with routine electronic monitoring.",
            }

    else:
        return {
            "action_type": "Review EOB",
            "channel": "Internal Ledger",
            "urgency": "Standard",
            "title": "Reconcile Remittance & Close Account",
            "description": "Verify payment posting against electronic remittance advice (835) and balance remaining patient responsibility.",
            "rationale": "Claim has completed adjudication cycle.",
        }


def get_claims_list(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    payer_id: Optional[str] = None,
    claim_status: Optional[str] = None,
    denial_status: Optional[str] = None,
    claim_type: Optional[str] = None,
    priority_band: Optional[str] = None,
    min_outstanding: Optional[float] = None,
    max_outstanding: Optional[float] = None,
    min_days_ar: Optional[int] = None,
    max_days_ar: Optional[int] = None,
    sort_by: str = "priority_score",
    sort_order: str = "desc",
) -> Tuple[List[dict], int, int]:
    """
    Retrieve paginated claims matching filter and search parameters, joined with ML predictions.
    """
    query = (
        db.query(Claim, Prediction)
        .join(Payer, Claim.payer_id == Payer.payer_id)
        .outerjoin(Prediction, Claim.claim_id == Prediction.claim_id)
    )

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Claim.claim_id.ilike(search_pattern),
                Claim.patient_id.ilike(search_pattern),
                Claim.provider_id.ilike(search_pattern),
                Claim.denial_reason.ilike(search_pattern),
                Claim.denial_code.ilike(search_pattern),
                Payer.payer_name.ilike(search_pattern),
            )
        )

    if payer_id:
        query = query.filter(Claim.payer_id == payer_id)
    if claim_status:
        query = query.filter(Claim.claim_status == claim_status)
    if denial_status:
        query = query.filter(Claim.denial_status == denial_status)
    if claim_type:
        query = query.filter(Claim.claim_type == claim_type)
    if priority_band:
        query = query.filter(Prediction.priority_band == priority_band)
    if min_outstanding is not None:
        query = query.filter(Claim.outstanding_amount >= min_outstanding)
    if max_outstanding is not None:
        query = query.filter(Claim.outstanding_amount <= max_outstanding)
    if min_days_ar is not None:
        query = query.filter(Claim.days_in_ar >= min_days_ar)
    if max_days_ar is not None:
        query = query.filter(Claim.days_in_ar <= max_days_ar)

    total_count = query.count()

    sort_col = ALLOWED_SORT_FIELDS.get(sort_by, Prediction.priority_score)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    total_pages = max(1, (total_count + page_size - 1) // page_size) if total_count > 0 else 1
    offset = (page - 1) * page_size

    results = query.offset(offset).limit(page_size).all()

    items = []
    for c, pred in results:
        del_p = pred.delay_probability if pred else 0.0
        den_p = pred.denial_probability if pred else 0.0
        rec_p = pred.recovery_probability if pred else 0.0
        score = pred.priority_score if pred else 0.0
        band = pred.priority_band if pred else "Low"
        exp_rec = pred.expected_recovery if pred else round(c.outstanding_amount * rec_p, 2)

        deadline_days = c.payer.filing_deadline_days if c.payer else 90
        contact = c.payer.preferred_contact_method if c.payer else "Payer Portal"

        rec_action = generate_recommended_action(
            claim_status=c.claim_status,
            denial_status=c.denial_status,
            denial_reason=c.denial_reason,
            denial_code=c.denial_code,
            days_in_ar=c.days_in_ar,
            filing_deadline_days=deadline_days,
            priority_band=band,
            preferred_contact=contact,
        )

        item = {
            "claim_id": c.claim_id,
            "patient_id": c.patient_id,
            "provider_id": c.provider_id,
            "payer_id": c.payer_id,
            "payer_name": c.payer.payer_name if c.payer else None,
            "claim_date": c.claim_date,
            "service_date": c.service_date,
            "claim_type": c.claim_type,
            "place_of_service": c.place_of_service,
            "billed_amount": c.billed_amount,
            "allowed_amount": c.allowed_amount,
            "paid_amount": c.paid_amount,
            "patient_responsibility": c.patient_responsibility,
            "outstanding_amount": c.outstanding_amount,
            "expected_reimbursement": c.expected_reimbursement,
            "claim_status": c.claim_status,
            "denial_status": c.denial_status,
            "denial_code": c.denial_code,
            "denial_reason": c.denial_reason,
            "days_in_ar": c.days_in_ar,
            "followup_count": c.followup_count,
            "resubmission_count": c.resubmission_count,
            "appeal_status": c.appeal_status,
            "authorization_required": c.authorization_required,
            "authorization_status": c.authorization_status,
            "network_status": c.network_status,
            "last_followup_date": c.last_followup_date,
            "last_payer_response": c.last_payer_response,
            "days_since_last_response": c.days_since_last_response,
            "delay_probability": del_p,
            "denial_probability": den_p,
            "recovery_probability": rec_p,
            "expected_recovery": exp_rec,
            "priority_score": score,
            "priority_band": band,
            "recommended_action": rec_action,
        }
        items.append(item)

    return items, total_count, total_pages


def get_claim_by_id(db: Session, claim_id: str) -> Optional[dict]:
    """Retrieve complete claim detail with relations, ML predictions, explainability, and recommended actions."""
    claim = (
        db.query(Claim)
        .options(
            joinedload(Claim.payer),
            joinedload(Claim.followups),
            joinedload(Claim.outcome),
            joinedload(Claim.prediction),
        )
        .filter(Claim.claim_id == claim_id.strip())
        .first()
    )
    if not claim:
        return None

    # Sort followups chronologically descending
    if claim.followups:
        claim.followups.sort(key=lambda f: f.followup_date or "", reverse=True)

    pred = claim.prediction
    if pred:
        del_p = pred.delay_probability
        den_p = pred.denial_probability
        rec_p = pred.recovery_probability
        exp_rec = pred.expected_recovery
        score = pred.priority_score
        band = pred.priority_band
    else:
        eval_res = evaluate_and_score_claim({
            "claim_id": claim.claim_id,
            "days_in_ar": claim.days_in_ar,
            "outstanding_amount": claim.outstanding_amount,
            "billed_amount": claim.billed_amount,
            "allowed_amount": claim.allowed_amount,
            "paid_amount": claim.paid_amount,
            "patient_responsibility": claim.patient_responsibility,
            "expected_reimbursement": claim.expected_reimbursement,
            "followup_count": claim.followup_count,
            "resubmission_count": claim.resubmission_count,
            "days_since_last_response": claim.days_since_last_response,
            "avg_processing_days": claim.payer.avg_processing_days if claim.payer else 15,
            "avg_response_days": claim.payer.avg_response_days if claim.payer else 7,
            "filing_deadline_days": claim.payer.filing_deadline_days if claim.payer else 90,
            "payer_id": claim.payer_id,
            "payer_name": claim.payer.payer_name if claim.payer else None,
            "claim_type": claim.claim_type,
            "place_of_service": claim.place_of_service,
            "claim_status": claim.claim_status,
            "denial_status": claim.denial_status,
            "denial_code": claim.denial_code,
            "denial_reason": claim.denial_reason,
            "authorization_required": str(claim.authorization_required),
            "authorization_status": claim.authorization_status,
            "network_status": claim.network_status,
            "appeal_status": claim.appeal_status,
        })
        del_p = eval_res["delay_probability"]
        den_p = eval_res["denial_probability"]
        rec_p = eval_res["recovery_probability"]
        exp_rec = eval_res["expected_recovery"]
        score = eval_res["priority_score"]
        band = eval_res["priority_band"]

    deadline_days = claim.payer.filing_deadline_days if claim.payer else 90
    remaining_deadline = max(0, deadline_days - claim.days_in_ar)
    contact = claim.payer.preferred_contact_method if claim.payer else "Payer Portal"

    reasons = generate_explainability_factors(
        claim_dict={
            "claim_id": claim.claim_id,
            "outstanding_amount": claim.outstanding_amount,
            "days_in_ar": claim.days_in_ar,
            "followup_count": claim.followup_count,
            "denial_reason": claim.denial_reason,
            "denial_code": claim.denial_code,
            "payer_name": claim.payer.payer_name if claim.payer else None,
            "filing_deadline_days": deadline_days,
            "avg_response_days": claim.payer.avg_response_days if claim.payer else 7,
            "authorization_status": claim.authorization_status,
        },
        delay_prob=del_p,
        denial_prob=den_p,
        recovery_prob=rec_p,
        expected_recovery=exp_rec,
        priority_score=score,
        priority_band=band,
    )

    rec_action = generate_recommended_action(
        claim_status=claim.claim_status,
        denial_status=claim.denial_status,
        denial_reason=claim.denial_reason,
        denial_code=claim.denial_code,
        days_in_ar=claim.days_in_ar,
        filing_deadline_days=deadline_days,
        priority_band=band,
        preferred_contact=contact,
    )

    return {
        "claim": claim,
        "delay_probability": del_p,
        "denial_probability": den_p,
        "recovery_probability": rec_p,
        "expected_recovery": exp_rec,
        "priority_score": score,
        "priority_band": band,
        "explainability_reasons": reasons,
        "recommended_action": rec_action,
        "filing_deadline_remaining_days": remaining_deadline,
    }


def get_priority_claims(
    db: Session,
    limit: int = 50,
    payer_id: Optional[str] = None,
    priority_band: Optional[str] = None,
) -> List[dict]:
    """
    Retrieve claims prioritized by ML priority score (0-100), financial impact, and AR risk.
    """
    query = (
        db.query(Claim, Prediction)
        .join(Payer, Claim.payer_id == Payer.payer_id)
        .join(Prediction, Claim.claim_id == Prediction.claim_id)
        .filter(Claim.claim_status.in_(["Pending", "Appeal Pending", "In Review", "Denied"]))
        .filter(Claim.outstanding_amount > 0)
    )

    if payer_id:
        query = query.filter(Claim.payer_id == payer_id)
    if priority_band:
        query = query.filter(Prediction.priority_band == priority_band)

    results = (
        query.order_by(desc(Prediction.priority_score), desc(Claim.outstanding_amount))
        .limit(limit)
        .all()
    )

    items = []
    for c, pred in results:
        deadline_days = c.payer.filing_deadline_days if c.payer else 90
        contact = c.payer.preferred_contact_method if c.payer else "Payer Portal"

        reasons = generate_explainability_factors(
            claim_dict={
                "claim_id": c.claim_id,
                "outstanding_amount": c.outstanding_amount,
                "days_in_ar": c.days_in_ar,
                "followup_count": c.followup_count,
                "denial_reason": c.denial_reason,
                "denial_code": c.denial_code,
                "payer_name": c.payer.payer_name if c.payer else None,
                "filing_deadline_days": deadline_days,
                "avg_response_days": c.payer.avg_response_days if c.payer else 7,
                "authorization_status": c.authorization_status,
            },
            delay_prob=pred.delay_probability,
            denial_prob=pred.denial_probability,
            recovery_prob=pred.recovery_probability,
            expected_recovery=pred.expected_recovery,
            priority_score=pred.priority_score,
            priority_band=pred.priority_band,
        )

        rec_action = generate_recommended_action(
            claim_status=c.claim_status,
            denial_status=c.denial_status,
            denial_reason=c.denial_reason,
            denial_code=c.denial_code,
            days_in_ar=c.days_in_ar,
            filing_deadline_days=deadline_days,
            priority_band=pred.priority_band,
            preferred_contact=contact,
        )

        items.append({
            "claim_id": c.claim_id,
            "patient_id": c.patient_id,
            "provider_id": c.provider_id,
            "payer_id": c.payer_id,
            "payer_name": c.payer.payer_name if c.payer else None,
            "claim_date": c.claim_date,
            "service_date": c.service_date,
            "claim_type": c.claim_type,
            "place_of_service": c.place_of_service,
            "billed_amount": c.billed_amount,
            "allowed_amount": c.allowed_amount,
            "paid_amount": c.paid_amount,
            "patient_responsibility": c.patient_responsibility,
            "outstanding_amount": c.outstanding_amount,
            "expected_reimbursement": c.expected_reimbursement,
            "claim_status": c.claim_status,
            "denial_status": c.denial_status,
            "denial_code": c.denial_code,
            "denial_reason": c.denial_reason,
            "days_in_ar": c.days_in_ar,
            "followup_count": c.followup_count,
            "resubmission_count": c.resubmission_count,
            "appeal_status": c.appeal_status,
            "authorization_required": c.authorization_required,
            "authorization_status": c.authorization_status,
            "network_status": c.network_status,
            "last_followup_date": c.last_followup_date,
            "last_payer_response": c.last_payer_response,
            "days_since_last_response": c.days_since_last_response,
            "delay_probability": pred.delay_probability,
            "denial_probability": pred.denial_probability,
            "recovery_probability": pred.recovery_probability,
            "expected_recovery": pred.expected_recovery,
            "priority_score": pred.priority_score,
            "priority_band": pred.priority_band,
            "explainability_reasons": reasons,
            "recommended_action": rec_action,
        })

    return items
