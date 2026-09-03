"""
AR Follow-Up AI - Dashboard & Analytics Service (Phase 6)

Calculates real-time KPIs, AR Aging buckets, Payer Performance metrics,
Denial Reasons breakdown, and Priority Distribution directly from SQLite database.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc

from backend.app.models import Claim, Prediction, ClaimOutcome, Payer


def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
    """
    Computes top-level KPI metrics across the entire 10,000 claim portfolio.
    """
    claim_stats = db.query(
        func.sum(Claim.outstanding_amount).label("total_ar"),
        func.count(Claim.claim_id).label("total_claims"),
        func.avg(Claim.days_in_ar).label("avg_days_ar"),
        func.sum(case((Claim.denial_status == "Denied", 1), else_=0)).label("denied_claims")
    ).first()

    exp_rec = db.query(func.sum(Prediction.expected_recovery)).scalar() or 0.0
    
    crit_claims = (
        db.query(func.count(Prediction.prediction_id))
        .filter(Prediction.priority_band == "Critical")
        .scalar() or 0
    )

    high_claims = (
        db.query(func.count(Prediction.prediction_id))
        .filter(Prediction.priority_band == "High")
        .scalar() or 0
    )

    rec_rev = db.query(func.sum(ClaimOutcome.recovered_amount)).scalar() or 0.0

    total_claims = claim_stats.total_claims or 1
    total_ar = float(claim_stats.total_ar or 0.0)
    avg_days = float(claim_stats.avg_days_ar or 0.0)
    denied_count = int(claim_stats.denied_claims or 0)
    denial_rate = round((denied_count / total_claims) * 100.0, 2)

    return {
        "total_ar": round(total_ar, 2),
        "total_claims": total_claims,
        "critical_claims": crit_claims,
        "high_priority_claims": high_claims,
        "expected_recovery": round(float(exp_rec), 2),
        "recovered_revenue": round(float(rec_rev), 2),
        "avg_days_in_ar": round(avg_days, 1),
        "denial_rate": denial_rate,
    }


def get_ar_aging_buckets(db: Session) -> List[Dict[str, Any]]:
    """
    Computes AR Aging distribution across standard healthcare aging buckets:
    0–30, 31–60, 61–90, 91–120, 120+
    """
    buckets_def = [
        ("0–30 days", 0, 30),
        ("31–60 days", 31, 60),
        ("61–90 days", 61, 90),
        ("91–120 days", 91, 120),
        ("120+ days", 121, None),
    ]

    results = []
    for label, min_d, max_d in buckets_def:
        query = db.query(
            func.count(Claim.claim_id).label("count"),
            func.sum(Claim.outstanding_amount).label("total_outstanding"),
            func.sum(Prediction.expected_recovery).label("expected_recovery"),
        ).outerjoin(Prediction, Claim.claim_id == Prediction.claim_id)

        if max_d is not None:
            query = query.filter(Claim.days_in_ar >= min_d, Claim.days_in_ar <= max_d)
        else:
            query = query.filter(Claim.days_in_ar >= min_d)

        row = query.first()
        cnt = row.count or 0
        out_amt = float(row.total_outstanding or 0.0)
        exp_rec = float(row.expected_recovery or 0.0)

        results.append({
            "bucket": label,
            "min_days": min_d,
            "max_days": max_d,
            "count": cnt,
            "total_outstanding": round(out_amt, 2),
            "expected_recovery": round(exp_rec, 2),
        })

    return results


def get_payer_performance(db: Session) -> List[Dict[str, Any]]:
    """
    Computes payer metrics, outstanding volume, expected recoveries, and processing timelines.
    """
    payers = db.query(Payer).all()
    results = []

    for p in payers:
        stats = (
            db.query(
                func.count(Claim.claim_id).label("count"),
                func.sum(Claim.outstanding_amount).label("total_outstanding"),
                func.sum(Prediction.expected_recovery).label("expected_recovery"),
                func.sum(case((Claim.denial_status == "Denied", 1), else_=0)).label("denied_claims"),
            )
            .outerjoin(Prediction, Claim.claim_id == Prediction.claim_id)
            .filter(Claim.payer_id == p.payer_id)
            .first()
        )

        cnt = stats.count or 0
        out_amt = float(stats.total_outstanding or 0.0)
        exp_rec = float(stats.expected_recovery or 0.0)
        denied_cnt = int(stats.denied_claims or 0)
        denial_rt = round((denied_cnt / cnt * 100.0), 1) if cnt > 0 else 0.0

        results.append({
            "payer_id": p.payer_id,
            "payer_name": p.payer_name,
            "plan_type": p.plan_type,
            "total_claims": cnt,
            "total_outstanding": round(out_amt, 2),
            "expected_recovery": round(exp_rec, 2),
            "avg_processing_days": p.avg_processing_days,
            "avg_response_days": p.avg_response_days,
            "filing_deadline_days": p.filing_deadline_days,
            "denial_rate": denial_rt,
        })

    # Sort descending by total outstanding balance
    results.sort(key=lambda x: x["total_outstanding"], reverse=True)
    return results


def get_denial_reasons_breakdown(db: Session) -> List[Dict[str, Any]]:
    """
    Computes breakdown of denial reasons with claim volume and dollar exposure.
    """
    total_denied = (
        db.query(func.count(Claim.claim_id))
        .filter(Claim.denial_reason.isnot(None), Claim.denial_reason != "")
        .scalar() or 1
    )

    rows = (
        db.query(
            Claim.denial_reason,
            func.count(Claim.claim_id).label("count"),
            func.sum(Claim.outstanding_amount).label("total_outstanding"),
        )
        .filter(Claim.denial_reason.isnot(None), Claim.denial_reason != "")
        .group_by(Claim.denial_reason)
        .order_by(desc("count"))
        .all()
    )

    results = []
    for r in rows:
        cnt = r.count or 0
        out_amt = float(r.total_outstanding or 0.0)
        pct = round((cnt / total_denied) * 100.0, 1)

        results.append({
            "reason": r.denial_reason,
            "count": cnt,
            "total_outstanding": round(out_amt, 2),
            "percentage": pct,
        })

    return results


def get_priority_distribution(db: Session) -> List[Dict[str, Any]]:
    """
    Computes distribution of claims across Critical, High, Medium, Low priority bands.
    """
    total_claims = db.query(func.count(Prediction.prediction_id)).scalar() or 10000

    order_map = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
    rows = (
        db.query(
            Prediction.priority_band,
            func.count(Prediction.prediction_id).label("count"),
            func.sum(Claim.outstanding_amount).label("total_outstanding"),
            func.sum(Prediction.expected_recovery).label("expected_recovery"),
        )
        .join(Claim, Prediction.claim_id == Claim.claim_id)
        .group_by(Prediction.priority_band)
        .all()
    )

    results = []
    for r in rows:
        cnt = r.count or 0
        out_amt = float(r.total_outstanding or 0.0)
        exp_rec = float(r.expected_recovery or 0.0)
        pct = round((cnt / total_claims) * 100.0, 1)

        results.append({
            "band": r.priority_band,
            "count": cnt,
            "total_outstanding": round(out_amt, 2),
            "expected_recovery": round(exp_rec, 2),
            "percentage": pct,
        })

    results.sort(key=lambda x: order_map.get(x["band"], 99))
    return results
