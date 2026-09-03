import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.closed_loop.engine import closed_loop_engine


@pytest.fixture
def client():
    return TestClient(app)


def test_closed_loop_execution_lifecycle():
    """Verify autonomous closed-loop execution lifecycle across 5 high-priority claims."""
    db = SessionLocal()
    try:
        res = closed_loop_engine.run_autonomous_loop(
            db=db,
            batch_size=5,
            min_priority_band="High",
            action_quality="high",
        )

        assert res["total_processed"] == 5
        assert res["total_original_outstanding"] > 0.0
        assert res["total_recovered"] >= 0.0
        assert 0.0 <= res["recovery_yield_percentage"] <= 100.0
        assert "APPROVED_FULL" in res["outcomes_breakdown"]
        assert len(res["results"]) == 5

        for claim_res in res["results"]:
            assert claim_res["claim_id"].startswith("CLM")
            assert claim_res["chosen_action"] in ["Appeal", "Status Inquiry", "Resubmission", "Escalation"]
            assert claim_res["simulated_outcome"] in ["APPROVED_FULL", "APPROVED_PARTIAL", "ADDITIONAL_INFO_REQUIRED", "DENIAL_UPHELD"]
            assert "EFT-" in claim_res["remittance_reference"]
    finally:
        db.close()


def test_closed_loop_api_endpoints(client):
    """Verify POST /api/closed-loop/run and GET /api/closed-loop/summary."""
    # 1. Run loop for 3 claims
    post_res = client.post(
        "/api/closed-loop/run",
        json={
            "batch_size": 3,
            "min_priority_band": "High",
            "action_quality": "high",
        }
    )
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["total_processed"] == 3
    assert "updated_dashboard_total_ar" in data
    assert "updated_dashboard_recovered_revenue" in data

    # 2. Summary
    sum_res = client.get("/api/closed-loop/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["total_actions_executed"] >= 3
    assert sum_data["total_recovered_revenue"] > 0
