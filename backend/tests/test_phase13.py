import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models import Claim, Payer, ClaimOutcome, Prediction, AgentAction, Followup


@pytest.fixture
def client():
    return TestClient(app)


def test_e2e_system_health(client):
    """Verify system health, database connectivity, and dataset row counts."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "connected"
    assert data["counts"]["claims"] == 10000
    assert data["counts"]["payers"] == 10
    assert data["counts"]["payer_policies"] == 10


def test_e2e_full_lifecycle_integration(client):
    """
    Test complete lifecycle from Claim retrieval -> ML prediction -> RAG search ->
    AI Agent decision -> Follow-up generation -> Payer simulation -> Closed loop execution.
    """
    # 1. Claim Lookup
    claim_res = client.get("/api/claims/CLM0003394")
    assert claim_res.status_code == 200
    claim_data = claim_res.json()
    assert claim_data["claim_id"] == "CLM0003394"

    # 2. Prediction Check
    pred_res = client.post("/api/predictions/CLM0003394")
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert 0.0 <= pred_data["delay_probability"] <= 1.0
    assert 0.0 <= pred_data["denial_probability"] <= 1.0

    # 3. RAG Search
    rag_res = client.get("/api/rag/claim-context/CLM0003394")
    assert rag_res.status_code == 200
    assert len(rag_res.json()) > 0

    # 4. Agent Decision
    agent_res = client.post("/api/agent/decide/CLM0003394")
    assert agent_res.status_code == 200
    agent_data = agent_res.json()
    assert agent_data["recommended_action"] == "Appeal"

    # 5. Generator Preview
    gen_res = client.get("/api/generator/preview/CLM0003394")
    assert gen_res.status_code == 200
    assert gen_res.json()["appeal_letter"] is not None

    # 6. Payer Simulation
    sim_res = client.post(
        "/api/simulator/simulate",
        json={
            "claim_id": "CLM0003394",
            "action_type": "Appeal",
            "action_quality": "high",
            "apply_to_db": False,
        }
    )
    assert sim_res.status_code == 200
    assert sim_res.json()["simulated_outcome"] in ["APPROVED_FULL", "APPROVED_PARTIAL", "ADDITIONAL_INFO_REQUIRED", "DENIAL_UPHELD"]

    # 7. Closed Loop Engine
    loop_res = client.post(
        "/api/closed-loop/run",
        json={
            "batch_size": 2,
            "min_priority_band": "High",
            "action_quality": "high",
        }
    )
    assert loop_res.status_code == 200
    assert loop_res.json()["total_processed"] == 2
