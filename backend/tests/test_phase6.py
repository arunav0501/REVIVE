import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_dashboard_metrics_endpoint(client):
    """Verify GET /api/dashboard/metrics returns accurate aggregate KPIs."""
    response = client.get("/api/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()

    assert data["total_claims"] == 10000
    assert data["total_ar"] > 40_000_000.0
    assert data["expected_recovery"] > 20_000_000.0
    assert data["recovered_revenue"] > 10_000_000.0
    assert 50.0 <= data["avg_days_in_ar"] <= 100.0
    assert 0.0 <= data["denial_rate"] <= 100.0
    assert data["critical_claims"] >= 0
    assert data["high_priority_claims"] > 0


def test_dashboard_ar_aging_endpoint(client):
    """Verify GET /api/dashboard/aging returns all 5 standard healthcare AR aging buckets."""
    response = client.get("/api/dashboard/aging")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 5
    bucket_names = [b["bucket"] for b in data]
    assert "0–30 days" in bucket_names
    assert "31–60 days" in bucket_names
    assert "61–90 days" in bucket_names
    assert "91–120 days" in bucket_names
    assert "120+ days" in bucket_names

    total_claims = sum(b["count"] for b in data)
    assert total_claims == 10000


def test_dashboard_payer_performance_endpoint(client):
    """Verify GET /api/dashboard/payer-performance returns 10 payers with metrics."""
    response = client.get("/api/dashboard/payer-performance")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 10
    for p in data:
        assert p["payer_id"].startswith("PAY")
        assert p["total_claims"] > 0
        assert p["total_outstanding"] > 0
        assert p["expected_recovery"] >= 0
        assert p["avg_processing_days"] > 0


def test_dashboard_denial_reasons_endpoint(client):
    """Verify GET /api/dashboard/denial-reasons returns ranked denial categories."""
    response = client.get("/api/dashboard/denial-reasons")
    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    for item in data:
        assert item["reason"] != ""
        assert item["count"] > 0
        assert item["total_outstanding"] > 0
        assert 0.0 <= item["percentage"] <= 100.0


def test_dashboard_priority_distribution_endpoint(client):
    """Verify GET /api/dashboard/priority-distribution returns all 4 priority bands."""
    response = client.get("/api/dashboard/priority-distribution")
    assert response.status_code == 200
    data = response.json()

    bands = {item["band"]: item for item in data}
    assert "Critical" in bands
    assert "High" in bands
    assert "Medium" in bands
    assert "Low" in bands

    total_claims = sum(item["count"] for item in data)
    assert total_claims == 10000
