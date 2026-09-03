from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models import Claim
from backend.app.rag.engine import rag_engine
from backend.app.schemas.rag import (
    RAGSearchRequest,
    RAGSearchResponse,
    PolicyChunkSchema,
    PayerPolicyFullSchema,
)

router = APIRouter(prefix="/rag", tags=["RAG Knowledge Engine"])


@router.get("/search", response_model=RAGSearchResponse)
def search_policy_knowledge_get(
    query: str = Query(..., min_length=2, description="Semantic or keyword query across payer policies"),
    payer_id: Optional[str] = Query(None, description="Optional payer filter (e.g. PAY001)"),
    top_k: int = Query(4, ge=1, le=10, description="Max matching chunks to return"),
):
    """
    Search payer policy vector knowledge base with semantic TF-IDF cosine similarity.
    """
    chunks = rag_engine.search(query=query, payer_id=payer_id, top_k=top_k)
    return RAGSearchResponse(
        query=query,
        payer_id=payer_id,
        results_count=len(chunks),
        chunks=[PolicyChunkSchema(**c) for c in chunks],
    )


@router.post("/search", response_model=RAGSearchResponse)
def search_policy_knowledge_post(payload: RAGSearchRequest):
    """
    POST search for payer policies and guidelines.
    """
    chunks = rag_engine.search(
        query=payload.query,
        payer_id=payload.payer_id,
        top_k=payload.top_k,
    )
    return RAGSearchResponse(
        query=payload.query,
        payer_id=payload.payer_id,
        results_count=len(chunks),
        chunks=[PolicyChunkSchema(**c) for c in chunks],
    )


@router.get("/policy/{payer_id}", response_model=PayerPolicyFullSchema)
def get_payer_policy_profile(payer_id: str):
    """
    Retrieve full policy document and all indexed knowledge chunks for a specific payer.
    """
    policy = rag_engine.get_payer_policy(payer_id=payer_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy knowledge for Payer '{payer_id}' not found",
        )
    return PayerPolicyFullSchema(**policy)


@router.get("/claim-context/{claim_id}", response_model=List[PolicyChunkSchema])
def get_claim_policy_context(claim_id: str, db: Session = Depends(get_db)):
    """
    Retrieve contextual policy chunks specifically relevant to a claim's denial reason, payer, and type.
    """
    claim = db.query(Claim).filter(Claim.claim_id == claim_id.strip()).first()
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim '{claim_id}' not found",
        )

    chunks = rag_engine.get_claim_context({
        "claim_id": claim.claim_id,
        "payer_id": claim.payer_id,
        "denial_reason": claim.denial_reason,
        "denial_code": claim.denial_code,
        "claim_type": claim.claim_type,
    }, top_k=4)

    return [PolicyChunkSchema(**c) for c in chunks]
