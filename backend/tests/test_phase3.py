import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_claims_pagination_default(client):
    """Test default pagination returns page 1 with 20 items and 10,000 total."""
    response = client.get("/api/claims")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 10000
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total_pages"] == 500
    assert len(data["items"]) == 20


def test_list_claims_custom_pagination(client):
    """Test custom page and page size."""
    response = client.get("/api/claims?page=3&page_size=50")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 3
    assert data["page_size"] == 50
    assert data["total_pages"] == 200
    assert len(data["items"]) == 50


def test_filter_claims_by_payer(client):
    """Test filtering by payer ID."""
    response = client.get("/api/claims?payer_id=PAY002&page_size=30")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(item["payer_id"] == "PAY002" for item in data["items"])


def test_filter_claims_by_status(client):
    """Test filtering by claim status."""
    response = client.get("/api/claims?claim_status=Appeal Pending&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert all(item["claim_status"] == "Appeal Pending" for item in data["items"])


def test_filter_claims_by_financial_range(client):
    """Test filtering by outstanding amount range."""
    response = client.get("/api/claims?min_outstanding=5000&max_outstanding=10000&page_size=25")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    for item in data["items"]:
        assert 5000 <= item["outstanding_amount"] <= 10000


def test_sort_claims(client):
    """Test sorting by outstanding amount descending."""
    response = client.get("/api/claims?sort_by=outstanding_amount&sort_order=desc&page_size=20")
    assert response.status_code == 200
    items = response.json()["items"]
    amounts = [item["outstanding_amount"] for item in items]
    assert amounts == sorted(amounts, reverse=True)


def test_search_claims(client):
    """Test searching by claim ID and denial reason keyword."""
    res1 = client.get("/api/claims?search=CLM0000001")
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["total"] >= 1
    assert any(item["claim_id"] == "CLM0000001" for item in data1["items"])

    res2 = client.get("/api/claims?search=Duplicate")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total"] > 0
    assert any("Duplicate" in (item["denial_reason"] or "") for item in data2["items"])


def test_get_single_claim_success(client):
    """Test retrieving single claim detail with relationships."""
    response = client.get("/api/claims/CLM0000001")
    assert response.status_code == 200
    data = response.json()
    assert data["claim_id"] == "CLM0000001"
    assert data["payer"] is not None
    assert data["payer"]["payer_id"] == "PAY001"
    assert data["outcome"] is not None
    assert data["outcome"]["final_outcome"] == "Denied"
    assert isinstance(data["followups"], list)


def test_get_single_claim_not_found(client):
    """Test 404 for invalid claim ID."""
    response = client.get("/api/claims/NON_EXISTENT_ID")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_get_priority_claims(client):
    """Test priority claims endpoint."""
    response = client.get("/api/claims/priority?limit=15")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 15
    assert all(item["outstanding_amount"] > 0 for item in items)
    # Verify sorting by priority score
    scores = [item["priority_score"] for item in items]
    assert scores == sorted(scores, reverse=True)
