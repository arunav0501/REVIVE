import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models import Claim, AgentAction, Followup
from backend.app.agent.followup_agent import followup_agent


@pytest.fixture
def client():
    return TestClient(app)


def test_agent_formulate_appeal_decision():
    """Verify agent formulates grounded appeal letter for denied claim."""
    db = SessionLocal()
    try:
        claim = db.query(Claim).filter(Claim.claim_id == "CLM0003394").first()
        assert claim is not None
        decision = followup_agent.formulate_decision(claim)

        assert decision["claim_id"] == "CLM0003394"
        assert decision["recommended_action"] == "Appeal"
        assert decision["urgency"] == "Immediate"
        assert decision["confidence"] >= 0.85
        assert "AetnaCare" in decision["generated_message"]
        assert "FORMAL FIRST-LEVEL RECONSIDERATION & APPEAL" in decision["generated_message"]
        assert decision["retrieved_policy_title"] != ""
    finally:
        db.close()


def test_agent_formulate_status_inquiry_decision():
    """Verify agent formulates status inquiry for non-denied claim."""
    db = SessionLocal()
    try:
        claim = db.query(Claim).filter(Claim.claim_status == "Pending").first()
        assert claim is not None
        decision = followup_agent.formulate_decision(claim)

        assert decision["claim_id"] == claim.claim_id
        assert decision["recommended_action"] in ["Status Inquiry", "Escalation"]
        assert len(decision["generated_message"]) > 100
    finally:
        db.close()


def test_agent_decide_api_endpoint(client):
    """Verify POST /api/agent/decide/{claim_id} endpoint."""
    response = client.post("/api/agent/decide/CLM0003394")
    assert response.status_code == 200
    data = response.json()
    assert data["claim_id"] == "CLM0003394"
    assert data["recommended_action"] == "Appeal"
    assert "generated_message" in data
    assert "reasoning" in data


def test_agent_execute_api_endpoint(client):
    """Verify POST /api/agent/execute/{claim_id} creates records and updates followups."""
    db = SessionLocal()
    try:
        claim = db.query(Claim).filter(Claim.claim_id == "CLM0000001").first()
        initial_fu_count = claim.followup_count or 0
    finally:
        db.close()

    response = client.post(
        "/api/agent/execute/CLM0000001",
        json={"simulate": True, "custom_message": "Automated simulated test message"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["claim_id"] == "CLM0000001"
    assert data["approval_status"] == "SIMULATED"

    # Verify db persistence
    db = SessionLocal()
    try:
        action = db.query(AgentAction).filter(AgentAction.action_id == data["action_id"]).first()
        assert action is not None
        assert action.claim_id == "CLM0000001"

        updated_claim = db.query(Claim).filter(Claim.claim_id == "CLM0000001").first()
        assert updated_claim.followup_count == initial_fu_count + 1
    finally:
        db.close()


def test_agent_list_actions_endpoint(client):
    """Verify GET /api/agent/actions endpoint."""
    response = client.get("/api/agent/actions?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "recommended_action" in data[0]
