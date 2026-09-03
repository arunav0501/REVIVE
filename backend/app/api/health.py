from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.database.session import get_db, check_db_connection
from backend.app.models import Claim, Payer, PayerPolicy, Followup, ClaimOutcome

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint verifying API and SQLite DB connection and table counts."""
    db_status = check_db_connection()
    
    counts = {}
    try:
        counts = {
            "claims": db.query(Claim).count(),
            "payers": db.query(Payer).count(),
            "payer_policies": db.query(PayerPolicy).count(),
            "followups": db.query(Followup).count(),
            "claim_outcomes": db.query(ClaimOutcome).count(),
        }
    except Exception:
        counts = {"error": "Unable to query table counts"}

    return {
        "status": "healthy" if db_status.get("status") == "connected" else "degraded",
        "app_name": "AR Follow-Up AI (RecoverAI)",
        "version": "1.0.0",
        "phase": 2,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "counts": counts,
    }


@router.get("/health/db")
def database_check(db: Session = Depends(get_db)):
    """Dedicated database connection test endpoint with row counts."""
    try:
        scalar = db.execute(text("SELECT 1")).scalar()
        counts = {
            "claims": db.query(Claim).count(),
            "payers": db.query(Payer).count(),
            "payer_policies": db.query(PayerPolicy).count(),
            "followups": db.query(Followup).count(),
            "claim_outcomes": db.query(ClaimOutcome).count(),
        }
        return {
            "status": "connected",
            "scalar_check": scalar,
            "counts": counts,
            "message": "SQLite database operational with verified datasets.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

