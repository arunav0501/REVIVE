import pytest
from backend.app.database.session import SessionLocal
from backend.app.models import Claim, Payer, PayerPolicy, Followup, ClaimOutcome



@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_database_table_counts(db_session):
    """Verify exact dataset counts in SQLite database."""
    assert db_session.query(Payer).count() == 10
    assert db_session.query(PayerPolicy).count() == 10
    assert db_session.query(Claim).count() == 10000
    assert db_session.query(Followup).count() >= 10000
    assert db_session.query(ClaimOutcome).count() == 10000


def test_claim_relationships(db_session):
    """Verify ORM relationships between Claim, Payer, Policy, Followup, and Outcome."""
    first_claim = db_session.query(Claim).filter_by(claim_id="CLM0000001").first()
    assert first_claim is not None
    assert first_claim.payer_id == "PAY001"
    assert first_claim.payer is not None
    assert first_claim.payer.payer_name == "BlueCross Health"

    # Payer policy relationship
    assert first_claim.payer.policy is not None
    assert first_claim.payer.policy.filing_deadline_days == 90

    # Outcome relationship
    assert first_claim.outcome is not None
    assert first_claim.outcome.final_outcome == "Denied"
    assert first_claim.outcome.was_denied == 1

    # Followup relationship
    claim_with_fu = db_session.query(Claim).filter_by(claim_id="CLM0003394").first()
    assert claim_with_fu is not None
    assert len(claim_with_fu.followups) >= 1
    assert any(fu.followup_id == "FU0000001" for fu in claim_with_fu.followups)


def test_claim_data_types_and_ranges(db_session):
    """Verify clean data types and numeric ranges."""
    sample_claims = db_session.query(Claim).limit(100).all()
    for c in sample_claims:
        assert isinstance(c.billed_amount, float)
        assert isinstance(c.allowed_amount, float)
        assert isinstance(c.outstanding_amount, float)
        assert isinstance(c.days_in_ar, int)
        assert isinstance(c.authorization_required, bool)
        assert c.outstanding_amount >= 0


def test_health_endpoints_with_dataset_counts(client):
    """Verify /health and /api/health/db report valid 10,000 dataset numbers."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["counts"]["claims"] == 10000
    assert data["counts"]["payers"] == 10
    assert data["counts"]["payer_policies"] == 10
    assert data["counts"]["followups"] >= 10000
    assert data["counts"]["claim_outcomes"] == 10000


    db_res = client.get("/api/health/db")
    assert db_res.status_code == 200
    db_data = db_res.json()
    assert db_data["status"] == "connected"
    assert db_data["counts"]["claims"] == 10000
