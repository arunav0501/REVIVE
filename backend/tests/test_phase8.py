import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.rag.engine import rag_engine


@pytest.fixture
def client():
    return TestClient(app)


def test_rag_engine_index_integrity():
    """Verify vector index contains all payer chunks across multiple domains."""
    assert rag_engine.is_indexed is True
    assert len(rag_engine.chunks) == 40  # 4 structured chunks x 10 payers
    payers = {c["payer_id"] for c in rag_engine.chunks}
    assert len(payers) == 10


def test_rag_semantic_search():
    """Verify semantic retrieval returns relevant documents with similarity scores."""
    results = rag_engine.search(query="prior authorization medical necessity appeal peer to peer", top_k=3)
    assert len(results) == 3
    for r in results:
        assert r["similarity_score"] > 0.0
        assert "payer_name" in r
        assert "content" in r


def test_rag_filtered_search():
    """Verify metadata filtering by payer ID."""
    results = rag_engine.search(query="timely filing deadline escalation", payer_id="PAY001", top_k=2)
    assert len(results) == 2
    assert all(r["payer_id"] == "PAY001" for r in results)


def test_rag_search_api_endpoint(client):
    """Verify GET /api/rag/search endpoint."""
    response = client.get("/api/rag/search?query=missing+information+documentation&top_k=4")
    assert response.status_code == 200
    data = response.json()
    assert data["results_count"] == 4
    assert len(data["chunks"]) == 4
    for chunk in data["chunks"]:
        assert "chunk_id" in chunk
        assert "content" in chunk
        assert chunk["similarity_score"] >= 0.0


def test_rag_payer_policy_endpoint(client):
    """Verify GET /api/rag/policy/{payer_id} endpoint."""
    response = client.get("/api/rag/policy/PAY001")
    assert response.status_code == 200
    data = response.json()
    assert data["payer_id"] == "PAY001"
    assert data["payer_name"] == "BlueCross Health"
    assert len(data["chunks"]) == 4


def test_rag_claim_context_endpoint(client):
    """Verify GET /api/rag/claim-context/{claim_id} returns targeted policy chunks."""
    response = client.get("/api/rag/claim-context/CLM0003394")
    assert response.status_code == 200
    chunks = response.json()
    assert len(chunks) > 0
    assert any("AetnaCare" in c["payer_name"] for c in chunks)
