"""
AR Follow-Up AI - Policy RAG Engine (Phase 8)

Loads payer policies from CSV, performs structured semantic chunking,
builds an in-memory TF-IDF + Cosine Similarity vector index,
and provides context retrieval for claims, appeals, and autonomous agents.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "payer_policies.csv"


class PolicyRAGEngine:
    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or CSV_PATH
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.is_indexed: bool = False
        self._load_and_index()

    def _load_and_index(self):
        """Loads payer policy CSV and generates chunked documents."""
        if not self.csv_path.exists():
            return

        df = pd.read_csv(self.csv_path)
        all_chunks = []

        for _, row in df.iterrows():
            payer_id = str(row.get("payer_id", "")).strip()
            payer_name = str(row.get("payer_name", "")).strip()
            deadline = int(row.get("filing_deadline_days", 90))
            contact = str(row.get("preferred_contact_method", "Portal")).strip()
            proc_days = int(row.get("average_processing_days", 15))
            resp_days = int(row.get("average_response_days", 7))
            docs = str(row.get("required_documents", "Itemized bill;Medical records")).strip()
            escalate_days = int(row.get("escalation_after_days", 10))
            policy_text = str(row.get("policy_text", "")).strip()

            # Chunk 1: Timely Filing, Adjudication & Escalation Limits
            c1_text = (
                f"{payer_name} ({payer_id}) Timely Filing & Escalation Guidelines: "
                f"Initial claims must be submitted within {deadline} calendar days from date of service. "
                f"Standard claim adjudication timeline is {proc_days} days. "
                f"Average follow-up response time is {resp_days} business days. "
                f"If a claim remains unpaid or unadjudicated past {escalate_days} days, submit an escalated inquiry via {contact}. "
                f"{policy_text}"
            )
            all_chunks.append({
                "chunk_id": f"{payer_id}_FILING_01",
                "payer_id": payer_id,
                "payer_name": payer_name,
                "topic": "Timely Filing & Adjudication",
                "title": f"{payer_name} Timely Filing & Processing Window",
                "content": c1_text,
                "required_documents": docs,
                "filing_deadline_days": deadline,
                "preferred_contact": contact,
            })

            # Chunk 2: Prior Authorization & Mandatory Clinical Documentation
            c2_text = (
                f"{payer_name} ({payer_id}) Clinical Documentation & Prior Authorization Rules: "
                f"Mandatory supporting documentation includes: {docs}. "
                f"For surgical and inpatient claims, include operative report and pre-service authorization certificate. "
                f"For diagnostic procedures, submit clinical chart notes, physician order, and eligibility proof. "
                f"Inquiries for missing information denials (CO-16) must attach complete medical records via {contact}."
            )
            all_chunks.append({
                "chunk_id": f"{payer_id}_DOCS_02",
                "payer_id": payer_id,
                "payer_name": payer_name,
                "topic": "Documentation & Authorization",
                "title": f"{payer_name} Required Documentation & Auth Policy",
                "content": c2_text,
                "required_documents": docs,
                "filing_deadline_days": deadline,
                "preferred_contact": contact,
            })

            # Chunk 3: Appeals, Disputes & Peer-to-Peer Resolution
            c3_text = (
                f"{payer_name} ({payer_id}) Appeals & Grievance Protocol: "
                f"First-level administrative appeals must be filed within {min(180, deadline + 60)} days of denial remittance advice. "
                f"Medical necessity disputes (CO-50) require peer-to-peer physician consultation or letter of clinical justification. "
                f"Duplicate claim disallowances (CO-18) require EOB reconciliation and distinct procedure modifier verification. "
                f"Submit formal appeals electronically through {contact}."
            )
            all_chunks.append({
                "chunk_id": f"{payer_id}_APPEAL_03",
                "payer_id": payer_id,
                "payer_name": payer_name,
                "topic": "Appeals & Dispute Resolution",
                "title": f"{payer_name} Appeal Process & Peer-to-Peer Guidelines",
                "content": c3_text,
                "required_documents": docs,
                "filing_deadline_days": deadline,
                "preferred_contact": contact,
            })

            # Chunk 4: Communication Channels & Contact Protocols
            c4_text = (
                f"{payer_name} ({payer_id}) Communication & Follow-Up Protocol: "
                f"Preferred contact channel for claims status and appeals is {contact}. "
                f"Direct follow-ups have an average response turnaround of {resp_days} days. "
                f"Escalation threshold is reached at {escalate_days} days without response. "
                f"Electronic transactions (EDI 276/277, 835 ERA) are supported."
            )
            all_chunks.append({
                "chunk_id": f"{payer_id}_CHANNEL_04",
                "payer_id": payer_id,
                "payer_name": payer_name,
                "topic": "Communication & Channel Protocol",
                "title": f"{payer_name} Preferred Contact & Channel Standards",
                "content": c4_text,
                "required_documents": docs,
                "filing_deadline_days": deadline,
                "preferred_contact": contact,
            })

        self.chunks = all_chunks

        # Fit TF-IDF Vector Index
        corpus = [c["content"] for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        self.is_indexed = True

    def search(
        self,
        query: str,
        payer_id: Optional[str] = None,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-k matching policy chunks using hybrid vector similarity and metadata filtering.
        """
        if not self.is_indexed or not self.vectorizer:
            return []

        query_vec = self.vectorizer.transform([query])
        sim_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        results = []
        for idx, score in enumerate(sim_scores):
            chunk = self.chunks[idx]

            # Metadata filter by payer if specified
            if payer_id and chunk["payer_id"] != payer_id.strip():
                continue

            # Boost exact payer name matches
            final_score = float(score)
            if payer_id and chunk["payer_id"] == payer_id.strip():
                final_score = min(1.0, final_score + 0.15)

            results.append({
                **chunk,
                "similarity_score": round(final_score, 4),
            })

        # Sort by similarity score descending
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    def get_payer_policy(self, payer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves full policy document and all chunks for a specific payer.
        """
        matching_chunks = [c for c in self.chunks if c["payer_id"] == payer_id.strip()]
        if not matching_chunks:
            return None

        first = matching_chunks[0]
        return {
            "payer_id": first["payer_id"],
            "payer_name": first["payer_name"],
            "filing_deadline_days": first["filing_deadline_days"],
            "preferred_contact_method": first["preferred_contact"],
            "average_processing_days": 18,
            "average_response_days": 7,
            "escalation_after_days": 12,
            "required_documents": first["required_documents"] or "Itemized bill;Medical records",
            "policy_text": f"Standard {first['payer_name']} operational policy with {first['filing_deadline_days']} days timely filing limit.",
            "chunks": [
                {**c, "similarity_score": 1.0} for c in matching_chunks
            ],
        }

    def get_claim_context(
        self,
        claim_dict: Dict[str, Any],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Generates contextual policy retrieval tailored specifically to a claim's denial reason and clinical profile.
        """
        payer_id = claim_dict.get("payer_id")
        denial_reason = claim_dict.get("denial_reason") or ""
        denial_code = claim_dict.get("denial_code") or ""
        claim_type = claim_dict.get("claim_type") or ""

        search_query = f"{claim_type} denial {denial_reason} {denial_code} appeal required documents timely filing"
        return self.search(query=search_query, payer_id=payer_id, top_k=top_k)


# Singleton RAG engine instance
rag_engine = PolicyRAGEngine()
