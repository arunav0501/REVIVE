import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models import Claim, Prediction
from backend.app.services.prioritization_service import (
    calculate_priority,
    generate_explainability_factors,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_predictions_table_populated(db_session):
    """Verify that predictions table in SQLite has 10,000 scored records."""
    assert db_session.query(Prediction).count() == 10000


def test_calculate_priority_bands():
    """Verify priority score weighting and band classifications."""
    # Critical test (High recovery, high delay, high outstanding)
    score_crit, band_crit, exp_crit = calculate_priority(
        outstanding_amount=45000.0,
        recovery_probability=0.90,
        delay_probability=0.90,
    )
    assert 85.0 <= score_crit <= 100.0
    assert band_crit == "Critical"
    assert exp_crit == 40500.0

    # Low test
    score_low, band_low, exp_low = calculate_priority(
        outstanding_amount=100.0,
        recovery_probability=0.20,
        delay_probability=0.10,
    )
    assert score_low < 40.0
    assert band_low == "Low"
    assert exp_low == 20.0


def test_generate_explainability_factors():
    """Verify explainability engine generates factual, relevant factors."""
    sample = {
        "claim_id": "CLM_EXP_TEST",
        "outstanding_amount": 22400.0,
        "days_in_ar": 78,
        "followup_count": 4,
        "denial_reason": "Medical necessity",
        "denial_code": "CO-50",
        "payer_name": "Molina Health",
        "filing_deadline_days": 90,
        "avg_response_days": 9,
        "authorization_status": "Denied",
    }
    reasons = generate_explainability_factors(
        claim_dict=sample,
        delay_prob=0.88,
        denial_prob=0.74,
        recovery_prob=0.65,
        expected_recovery=14560.0,
        priority_score=81.5,
        priority_band="High",
    )
    assert len(reasons) >= 3
    assert any("22,400" in r for r in reasons)
    assert any("78 days" in r for r in reasons)
    assert any("Medical necessity" in r for r in reasons)


def test_claims_list_with_ml_prioritization(client):
    """Verify GET /api/claims returns priority fields and sorts correctly."""
    response = client.get("/api/claims?sort_by=priority_score&sort_order=desc&page_size=20")
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    assert len(items) == 20
    for item in items:
        assert item["priority_score"] is not None
        assert item["priority_band"] in ["Critical", "High", "Medium", "Low"]
        assert item["expected_recovery"] is not None
        assert 0.0 <= item["priority_score"] <= 100.0

    scores = [item["priority_score"] for item in items]
    assert scores == sorted(scores, reverse=True)


def test_filter_claims_by_priority_band(client):
    """Verify filtering by priority band."""
    response = client.get("/api/claims?priority_band=High&page_size=15")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(item["priority_band"] == "High" for item in data["items"])


def test_priority_endpoint_with_explainability(client):
    """Verify GET /api/claims/priority returns urgency queue with explainability reasons."""
    response = client.get("/api/claims/priority?limit=10")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 10
    for item in items:
        assert item["priority_score"] is not None
        assert item["priority_band"] is not None
        assert len(item["explainability_reasons"]) > 0


def test_single_claim_detail_with_explainability(client, db_session):
    """Verify GET /api/claims/{claim_id} includes explainability factors."""
    claim = db_session.query(Claim).first()
    assert claim is not None

    response = client.get(f"/api/claims/{claim.claim_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["priority_score"] is not None
    assert data["priority_band"] in ["Critical", "High", "Medium", "Low"]
    assert data["explainability_reasons"] is not None
    assert len(data["explainability_reasons"]) > 0
