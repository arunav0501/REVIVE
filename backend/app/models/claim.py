from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


class Payer(Base):
    __tablename__ = "payers"

    payer_id = Column(String(50), primary_key=True, index=True)
    payer_name = Column(String(255), nullable=False)
    plan_type = Column(String(100), nullable=False)
    avg_processing_days = Column(Integer, nullable=False, default=15)
    avg_response_days = Column(Integer, nullable=False, default=7)
    filing_deadline_days = Column(Integer, nullable=False, default=90)
    preferred_contact_method = Column(String(50), nullable=False, default="Portal")

    # Relationships
    claims = relationship("Claim", back_populates="payer", lazy="select")
    policy = relationship("PayerPolicy", back_populates="payer", uselist=False, lazy="select")


class PayerPolicy(Base):
    __tablename__ = "payer_policies"

    payer_id = Column(String(50), ForeignKey("payers.payer_id"), primary_key=True, index=True)
    payer_name = Column(String(255), nullable=False)
    policy_document = Column(String(255), nullable=False)
    filing_deadline_days = Column(Integer, nullable=False)
    preferred_contact_method = Column(String(50), nullable=False)
    average_processing_days = Column(Integer, nullable=False)
    average_response_days = Column(Integer, nullable=False)
    required_documents = Column(Text, nullable=True)
    escalation_after_days = Column(Integer, nullable=False)
    policy_text = Column(Text, nullable=False)

    # Relationship
    payer = relationship("Payer", back_populates="policy")


class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(String(50), primary_key=True, index=True)
    patient_id = Column(String(50), nullable=False, index=True)
    provider_id = Column(String(50), nullable=False, index=True)
    payer_id = Column(String(50), ForeignKey("payers.payer_id"), nullable=False, index=True)
    claim_date = Column(String(20), nullable=False, index=True)
    service_date = Column(String(20), nullable=False)
    claim_type = Column(String(50), nullable=False, index=True)
    place_of_service = Column(String(100), nullable=False)
    billed_amount = Column(Float, nullable=False, default=0.0)
    allowed_amount = Column(Float, nullable=False, default=0.0)
    paid_amount = Column(Float, nullable=False, default=0.0)
    patient_responsibility = Column(Float, nullable=False, default=0.0)
    outstanding_amount = Column(Float, nullable=False, default=0.0, index=True)
    expected_reimbursement = Column(Float, nullable=False, default=0.0)
    claim_status = Column(String(50), nullable=False, index=True)
    denial_status = Column(String(50), nullable=True, index=True)
    denial_code = Column(String(50), nullable=True, index=True)
    denial_reason = Column(String(255), nullable=True)
    days_in_ar = Column(Integer, nullable=False, default=0, index=True)
    followup_count = Column(Integer, nullable=False, default=0)
    resubmission_count = Column(Integer, nullable=False, default=0)
    appeal_status = Column(String(50), nullable=False, default="Not Applicable")
    authorization_required = Column(Boolean, nullable=False, default=False)
    authorization_status = Column(String(50), nullable=False, default="Not Required")
    network_status = Column(String(50), nullable=False, default="In-Network")
    last_followup_date = Column(String(20), nullable=True)
    last_payer_response = Column(String(255), nullable=True)
    days_since_last_response = Column(Integer, nullable=True)

    # Relationships
    payer = relationship("Payer", back_populates="claims")
    followups = relationship("Followup", back_populates="claim", cascade="all, delete-orphan", lazy="select")
    outcome = relationship("ClaimOutcome", back_populates="claim", uselist=False, cascade="all, delete-orphan", lazy="select")
    prediction = relationship("Prediction", back_populates="claim", uselist=False, cascade="all, delete-orphan", lazy="select")
    agent_actions = relationship("AgentAction", back_populates="claim", cascade="all, delete-orphan", lazy="select")


class Followup(Base):
    __tablename__ = "followups"

    followup_id = Column(String(50), primary_key=True, index=True)
    claim_id = Column(String(50), ForeignKey("claims.claim_id"), nullable=False, index=True)
    followup_date = Column(String(20), nullable=False, index=True)
    channel = Column(String(50), nullable=False)
    action_type = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    payer_response = Column(String(255), nullable=True)
    response_date = Column(String(20), nullable=True)
    outcome = Column(String(100), nullable=True)

    # Relationship
    claim = relationship("Claim", back_populates="followups")


class ClaimOutcome(Base):
    __tablename__ = "claim_outcomes"

    claim_id = Column(String(50), ForeignKey("claims.claim_id"), primary_key=True, index=True)
    final_outcome = Column(String(50), nullable=False, index=True)
    days_to_resolution = Column(Integer, nullable=False, default=0)
    was_denied = Column(Integer, nullable=False, default=0)
    was_delayed = Column(Integer, nullable=False, default=0)
    recovered_amount = Column(Float, nullable=False, default=0.0)
    successful_followup = Column(Integer, nullable=False, default=0)

    # Relationship
    claim = relationship("Claim", back_populates="outcome")


class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String(50), ForeignKey("claims.claim_id"), unique=True, nullable=False, index=True)
    denial_probability = Column(Float, nullable=False, default=0.0)
    delay_probability = Column(Float, nullable=False, default=0.0)
    recovery_probability = Column(Float, nullable=False, default=0.0)
    expected_recovery = Column(Float, nullable=False, default=0.0)
    priority_score = Column(Float, nullable=False, default=0.0, index=True)
    priority_band = Column(String(20), nullable=False, default="Low", index=True)
    model_version = Column(String(50), nullable=False, default="1.0.0")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    claim = relationship("Claim", back_populates="prediction")


class AgentAction(Base):
    __tablename__ = "agent_actions"

    action_id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(String(50), ForeignKey("claims.claim_id"), nullable=False, index=True)
    recommended_action = Column(String(100), nullable=False)
    reasoning = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True)
    retrieved_policy = Column(Text, nullable=True)
    generated_message = Column(Text, nullable=True)
    approval_status = Column(String(50), nullable=False, default="PENDING")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship
    claim = relationship("Claim", back_populates="agent_actions")


# Helpful compound indexes
Index("ix_claims_payer_status", Claim.payer_id, Claim.claim_status)
Index("ix_claims_status_days_ar", Claim.claim_status, Claim.days_in_ar)
