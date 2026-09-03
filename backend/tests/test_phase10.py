import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models import Claim
from backend.app.generator.artifact_generator import artifact_generator


@pytest.fixture
def client():
    return TestClient(app)


def test_generator_appeal_letter_content():
    """Verify appeal letter generation contains required formal sections and metadata."""
    db = SessionLocal()
    try:
        claim = db.query(Claim).filter(Claim.claim_id == "CLM0003394").first()
        assert claim is not None
        result = artifact_generator.generate(claim, artifact_type="appeal_letter", tone="urgent")

        assert result["claim_id"] == "CLM0003394"
        assert result["appeal_letter"] is not None
        assert "FORMAL FIRST-LEVEL RECONSIDERATION & APPEAL" in result["appeal_letter"]
        assert "CLM0003394" in result["appeal_letter"]
        assert "PT010106" in result["appeal_letter"]
        assert "AetnaCare" in result["appeal_letter"]
        assert "PAYER POLICY GROUNDING" in result["appeal_letter"]
        assert "Exhibit A:" in result["appeal_letter"]
        assert "EXPEDITED REVIEW REQUESTED" in result["appeal_letter"]
    finally:
        db.close()


def test_generator_all_formats():
    """Verify all 5 formats are produced when artifact_type is 'all'."""
    db = SessionLocal()
    try:
        claim = db.query(Claim).filter(Claim.claim_id == "CLM0003394").first()
        result = artifact_generator.generate(claim, artifact_type="all")

        assert result["appeal_letter"] is not None
        assert result["portal_message"] is not None
        assert result["phone_script"] is not None
        assert result["email_template"] is not None
        assert result["edi_resubmission_note"] is not None

        # Verify portal message
        assert "SECURE PROVIDER PORTAL INQUIRY" in result["portal_message"]
        # Verify phone script
        assert "CALL CENTER AGENT PHONE SCRIPT" in result["phone_script"]
        # Verify email template
        assert "SECURE HIPAA-COMPLIANT EMAIL TEMPLATE" in result["email_template"]
        # Verify EDI note
        assert "ELECTRONIC RESUBMISSION PACKET (EDI 837" in result["edi_resubmission_note"]
    finally:
        db.close()


def test_generator_different_denial_scenarios():
    """Verify generator tailors text for different denial codes."""
    db = SessionLocal()
    try:
        # Find or test multiple claims
        claims = db.query(Claim).filter(Claim.denial_code.isnot(None)).limit(5).all()
        for c in claims:
            res = artifact_generator.generate(c, artifact_type="appeal_letter")
            assert res["appeal_letter"] is not None
            assert c.denial_code in res["appeal_letter"]
    finally:
        db.close()


def test_generator_api_endpoints(client):
    """Verify POST /api/generator/generate and GET /api/generator/templates."""
    # 1. Post generate
    post_res = client.post(
        "/api/generator/generate",
        json={
            "claim_id": "CLM0003394",
            "artifact_type": "all",
            "tone": "firm",
            "custom_notes": "Urgent review requested by Dr. Miller",
        }
    )
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["claim_id"] == "CLM0003394"
    assert "Dr. Miller" in data["appeal_letter"]

    # 2. Preview
    prev_res = client.get("/api/generator/preview/CLM0003394")
    assert prev_res.status_code == 200

    # 3. Templates catalog
    tpl_res = client.get("/api/generator/templates")
    assert tpl_res.status_code == 200
    catalog = tpl_res.json()
    assert len(catalog["available_artifact_types"]) == 5
    assert len(catalog["scenarios"]) >= 5
