import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.claim_service import generate_recommended_action


@pytest.fixture
def client():
    return TestClient(app)


def test_recommended_action_generator():
    """Verify intelligent recommendation logic for different denial categories."""
    # Missing information denial
    action_missing = generate_recommended_action(
        claim_status="Denied",
        denial_status="Denied",
        denial_reason="Missing information",
        denial_code="CO-16",
        days_in_ar=75,
        filing_deadline_days=90,
        priority_band="Critical",
        preferred_contact="Portal",
    )
    assert action_missing["action_type"] == "Appeal"
    assert "CO-16" in action_missing["title"]
    assert "missing" in action_missing["description"].lower() or "documentation" in action_missing["description"].lower()

    # Medical necessity denial
    action_med = generate_recommended_action(
        claim_status="Denied",
        denial_status="Denied",
        denial_reason="Medical necessity",
        denial_code="CO-50",
        days_in_ar=40,
        filing_deadline_days=120,
        priority_band="High",
        preferred_contact="Phone",
    )
    assert "Peer-to-Peer" in action_med["title"]
    assert action_med["action_type"] == "Appeal"

    # Duplicate claim denial
    action_dup = generate_recommended_action(
        claim_status="Denied",
        denial_status="Denied",
        denial_reason="Duplicate claim",
        denial_code="CO-18",
        days_in_ar=50,
        filing_deadline_days=90,
        priority_band="Medium",
    )
    assert action_dup["action_type"] == "Resubmission"
    assert "Modifier" in action_dup["title"]


def test_claim_detail_full_payload(client):
    """Verify GET /api/claims/{claim_id} returns all 5 required Phase 7 components."""
    response = client.get("/api/claims/CLM0003394")
    assert response.status_code == 200
    data = response.json()

    # 1. Metadata
    assert data["claim_id"] == "CLM0003394"
    assert data["patient_id"] == "PT010106"
    assert data["provider_id"] == "PR0228"
    assert data["billed_amount"] > 0
    assert data["outstanding_amount"] > 0
    assert data["claim_type"] == "Diagnostic"

    # 2. Payer policy profile
    assert data["payer"] is not None
    assert data["payer"]["payer_name"] == "AetnaCare"
    assert data["payer"]["filing_deadline_days"] == 120
    assert data["filing_deadline_remaining_days"] >= 0

    # 3. Followup timeline
    assert isinstance(data["followups"], list)
    assert len(data["followups"]) >= 2
    assert all("followup_id" in f for f in data["followups"])
    assert all("channel" in f for f in data["followups"])

    # 4. ML Prediction & explainability
    assert 0.0 <= data["delay_probability"] <= 1.0
    assert 0.0 <= data["denial_probability"] <= 1.0
    assert 0.0 <= data["recovery_probability"] <= 1.0
    assert data["expected_recovery"] > 0
    assert len(data["explainability_reasons"]) > 0

    # 5. Recommended next action
    assert data["recommended_action"] is not None
    assert data["recommended_action"]["action_type"] in ["Appeal", "Resubmission", "Status Inquiry", "Review EOB"]
    assert len(data["recommended_action"]["title"]) > 0
    assert len(data["recommended_action"]["description"]) > 0
    assert len(data["recommended_action"]["rationale"]) > 0
