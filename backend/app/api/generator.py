from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Claim
from backend.app.generator.artifact_generator import artifact_generator
from backend.app.schemas.generator import (
    GenerateArtifactRequest,
    GeneratedArtifactsResponse,
    TemplateCatalogResponse,
    TemplateScenarioInfo,
)

router = APIRouter(prefix="/generator", tags=["Follow-Up Artifact Generator"])


@router.post("/generate", response_model=GeneratedArtifactsResponse)
def generate_followup_artifacts(
    payload: GenerateArtifactRequest,
    db: Session = Depends(get_db),
):
    """
    Generate customized, professional follow-up communication artifacts
    (Appeal Letters, Portal Inquiries, Phone Scripts, Email Templates, EDI Notes)
    grounded in claim clinical data and retrieved payer policy rules.
    """
    claim = db.query(Claim).filter(Claim.claim_id == payload.claim_id.strip()).first()
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{payload.claim_id}' not found",
        )

    results = artifact_generator.generate(
        claim=claim,
        artifact_type=payload.artifact_type or "all",
        tone=payload.tone or "firm",
        custom_notes=payload.custom_notes,
    )
    return GeneratedArtifactsResponse(**results)


@router.get("/preview/{claim_id}", response_model=GeneratedArtifactsResponse)
def preview_claim_artifacts(
    claim_id: str,
    tone: str = Query("firm", pattern="^(firm|urgent|collaborative)$"),
    db: Session = Depends(get_db),
):

    """
    Quick preview of all 5 artifact formats for a given claim.
    """
    claim = db.query(Claim).filter(Claim.claim_id == claim_id.strip()).first()
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' not found",
        )

    results = artifact_generator.generate(
        claim=claim,
        artifact_type="all",
        tone=tone,
    )
    return GeneratedArtifactsResponse(**results)


@router.get("/templates", response_model=TemplateCatalogResponse)
def get_template_catalog():
    """
    Returns available artifact template formats and supported denial scenarios.
    """
    return TemplateCatalogResponse(
        available_artifact_types=[
            "appeal_letter",
            "portal_message",
            "phone_script",
            "email_template",
            "edi_resubmission_note",
        ],
        scenarios=[
            TemplateScenarioInfo(
                scenario_name="Missing Information Documentation Appeal",
                denial_code="CO-16",
                description="Submits itemized billing records, physician chart notes, and operative reports to overturn CO-16 denials.",
                recommended_artifacts=["appeal_letter", "portal_message", "email_template"],
            ),
            TemplateScenarioInfo(
                scenario_name="Prior Authorization & Pre-Certification Dispute",
                denial_code="CO-197",
                description="Retroactive clinical pre-certification package with attending physician urgent necessity letters.",
                recommended_artifacts=["appeal_letter", "phone_script", "portal_message"],
            ),
            TemplateScenarioInfo(
                scenario_name="Medical Necessity Clinical Review & Peer-to-Peer",
                denial_code="CO-50",
                description="Exhaustive clinical justification and scheduling of peer-to-peer physician discussion.",
                recommended_artifacts=["appeal_letter", "phone_script"],
            ),
            TemplateScenarioInfo(
                scenario_name="Timely Filing Electronic Clearinghouse Proof",
                denial_code="CO-29",
                description="Provides clearinghouse EDI 999/277 timestamped acknowledgment proving timely transmission.",
                recommended_artifacts=["appeal_letter", "email_template"],
            ),
            TemplateScenarioInfo(
                scenario_name="Duplicate Service Procedural Modifier Correction",
                denial_code="CO-18",
                description="Audits separate surgical sites and compiles corrected electronic replacement claim (EDI 837).",
                recommended_artifacts=["edi_resubmission_note", "portal_message"],
            ),
        ],
    )
