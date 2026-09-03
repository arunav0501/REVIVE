import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml import predictor
from backend.app.database.session import SessionLocal
from backend.app.models import Claim


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


def test_model_artifacts_exist():
    """Verify saved models and metrics file exist."""
    models_dir = Path("backend/trained_models")
    assert (models_dir / "delay_model.joblib").exists()
    assert (models_dir / "denial_model.joblib").exists()
    assert (models_dir / "metrics.json").exists()


def test_predictor_loaded_and_evaluates():
    """Verify ML predictor loaded models and generates real probabilities."""
    assert predictor.is_loaded is True
    sample_claim = {
        "claim_id": "TEST_001",
        "days_in_ar": 75,
        "outstanding_amount": 12500.0,
        "billed_amount": 18000.0,
        "allowed_amount": 14000.0,
        "paid_amount": 1500.0,
        "patient_responsibility": 500.0,
        "expected_reimbursement": 11000.0,
        "followup_count": 3,
        "resubmission_count": 1,
        "days_since_last_response": 20,
        "avg_processing_days": 18,
        "avg_response_days": 7,
        "filing_deadline_days": 90,
        "payer_id": "PAY002",
        "claim_type": "Inpatient",
        "place_of_service": "Hospital",
        "claim_status": "Denied",
        "denial_status": "Denied",
        "denial_code": "CO-18",
        "denial_reason": "Duplicate claim",
        "authorization_required": "True",
        "authorization_status": "Approved",
        "network_status": "In-Network",
        "appeal_status": "Under Review",
    }

    result = predictor.predict_claim(sample_claim)
    assert 0.0 <= result["delay_probability"] <= 1.0
    assert 0.0 <= result["denial_probability"] <= 1.0
    assert 0.0 <= result["recovery_probability"] <= 1.0
    assert result["expected_recovery"] > 0
    assert result["expected_recovery"] == round(12500.0 * result["recovery_probability"], 2)


def test_get_metrics_endpoint(client):
    """Test GET /api/predictions/metrics endpoint returns valid evaluation metrics."""
    response = client.get("/api/predictions/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "delay_model" in data["models"]
    assert "denial_model" in data["models"]

    delay_m = data["models"]["delay_model"]["metrics"]
    denial_m = data["models"]["denial_model"]["metrics"]

    assert delay_m["roc_auc"] > 0.60
    assert delay_m["accuracy"] > 0.60
    assert denial_m["roc_auc"] > 0.60
    assert denial_m["accuracy"] > 0.60


def test_predict_single_claim_endpoint(client, db_session):
    """Test POST /api/predictions/{claim_id} endpoint."""
    claim = db_session.query(Claim).first()
    assert claim is not None

    response = client.post(f"/api/predictions/{claim.claim_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["claim_id"] == claim.claim_id
    assert 0.0 <= data["delay_probability"] <= 1.0
    assert 0.0 <= data["denial_probability"] <= 1.0
    assert 0.0 <= data["recovery_probability"] <= 1.0
    assert data["expected_recovery"] >= 0.0


def test_predict_single_claim_404(client):
    """Test 404 for invalid claim ID in prediction endpoint."""
    response = client.post("/api/predictions/NON_EXISTENT_ID")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_predict_batch_claims_endpoint(client, db_session):
    """Test POST /api/predictions/batch endpoint."""
    claims = db_session.query(Claim).limit(5).all()
    claim_ids = [c.claim_id for c in claims]

    response = client.post("/api/predictions/batch", json={"claim_ids": claim_ids})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    for item in data:
        assert item["claim_id"] in claim_ids
        assert 0.0 <= item["delay_probability"] <= 1.0
        assert 0.0 <= item["denial_probability"] <= 1.0
        assert 0.0 <= item["recovery_probability"] <= 1.0
