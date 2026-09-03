from typing import List, Optional
from pydantic import BaseModel


class PolicyChunkSchema(BaseModel):
    chunk_id: str
    payer_id: str
    payer_name: str
    topic: str
    title: str
    content: str
    required_documents: Optional[str] = None
    filing_deadline_days: int
    preferred_contact: str
    similarity_score: float


class RAGSearchRequest(BaseModel):
    query: str
    payer_id: Optional[str] = None
    top_k: int = 4


class RAGSearchResponse(BaseModel):
    query: str
    payer_id: Optional[str] = None
    results_count: int
    chunks: List[PolicyChunkSchema]


class PayerPolicyFullSchema(BaseModel):
    payer_id: str
    payer_name: str
    filing_deadline_days: int
    preferred_contact_method: str
    average_processing_days: int
    average_response_days: int
    escalation_after_days: int
    required_documents: str
    policy_text: str
    chunks: List[PolicyChunkSchema]
