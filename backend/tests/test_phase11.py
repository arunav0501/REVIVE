import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models import Claim
from backend.app.simulator.payer_simulator import payer_simulator


@pytest.fixture
def client():
    return TestClient(app)


def test_simulator_probability_distribution():
    """Verify probability distribution sums to 1.0 and responds to quality modifiers."""
    db = SessionLocal()
    try:
        claim = db.query(Claim).filter(Claim.claim_id == "CLM0003394").first()
        assert claim is not None

        probs_high = payer_simulator.calculate_probability_distribution(claim, action_type="Appeal", action_quality="high")
        sum_high = sum(probs_high.values())
        assert pytest.approx(sum_high, 0.01) == 1.0
        assert probs_high["p_approved_full"] > 0.30

        probs_low = payer_simulator.calculate_probability_distribution(claim, action_type="Appeal", action_quality="low")
        sum_low = sum(probs_low.values())
        assert pytest.approx(sum_low, 0.01) == 1.0
        # High quality should have higher full approval probability than low quality
        assert probs_high["p_approved_full"] > probs_low["p_approved_full"]
    finally:
        db.close()


def test_simulator_outcomes_and_text():
    """Verify simulated response generates valid outcome, amounts, and remittance text."""
    db = SessionLocal()
    try:
        claim = db.query(Claim).filter(Claim.claim_id == "CLM0003394").first()
        res = payer_simulator.simulate_response(claim, action_type="Appeal", action_quality="high", seed=42)

        assert res["claim_id"] == "CLM0003394"
        assert res["payer_name"] == "AetnaCare"
        assert res["simulated_outcome"] in ["APPROVED_FULL", "APPROVED_PARTIAL", "ADDITIONAL_INFO_REQUIRED", "DENIAL_UPHELD"]
        assert len(res["payer_response_text"]) > 20
        assert "EFT-" in res["remittance_reference"]
        assert res["turnaround_days"] >= 2

        if res["simulated_outcome"] == "APPROVED_FULL":
            assert res["recovered_amount"] == claim.outstanding_amount
            assert res["remaining_outstanding"] == 0.0
        elif res["simulated_outcome"] == "APPROVED_PARTIAL":
            assert 0.0 < res["recovered_amount"] < claim.outstanding_amount
        else:
            assert res["recovered_amount"] == 0.0
    finally:
        db.close()


def test_simulator_api_endpoints(client):
    """Verify POST /api/simulator/simulate, GET /api/simulator/probabilities, and POST /api/simulator/batch."""
    # 1. Single claim simulate
    post_res = client.post(
        "/api/simulator/simulate",
        json={
            "claim_id": "CLM0003394",
            "action_type": "Appeal",
            "action_quality": "high",
            "apply_to_db": False,
        }
    )
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["claim_id"] == "CLM0003394"
    assert data["simulated_outcome"] in ["APPROVED_FULL", "APPROVED_PARTIAL", "ADDITIONAL_INFO_REQUIRED", "DENIAL_UPHELD"]
    assert "probability_distribution" in data

    # 2. Get probabilities
    prob_res = client.get("/api/simulator/probabilities/CLM0003394?action_type=Appeal&action_quality=high")
    assert prob_res.status_code == 200
    prob_data = prob_res.json()
    assert "p_approved_full" in prob_data
    assert "p_denial_upheld" in prob_data

    # 3. Batch simulate
    batch_res = client.post(
        "/api/simulator/batch",
        json={
            "claim_ids": ["CLM0003394", "CLM0000001", "CLM0000005"],
            "action_type": "Appeal",
            "apply_to_db": False,
        }
    )
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert batch_data["total_simulated"] >= 2
    assert "outcomes_breakdown" in batch_data
