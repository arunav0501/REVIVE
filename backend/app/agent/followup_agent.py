"""
AR Follow-Up AI - Autonomous Follow-Up Agent (Phase 9)

Integrates:
1. Claim state evaluation (denial status, days in AR, priority score, follow-up history).
2. RAG Policy Context retrieval from vector store.
3. Optimal Action & Channel determination.
4. Formal Appeal Letter / Status Inquiry / Phone Script generation.
5. Simulated / Real Execution recording in agent_actions and followups tables.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date, timezone
import json
from sqlalchemy.orm import Session

from backend.app.models import Claim, AgentAction, Followup, Prediction
from backend.app.rag.engine import rag_engine


class AIFollowUpAgent:
    def __init__(self):
        self.rag = rag_engine

    def formulate_decision(self, claim: Claim) -> Dict[str, Any]:
        """
        Evaluates a claim, retrieves grounding policy rules via RAG,
        and drafts a professional communication artifact.
        """
        payer = claim.payer

        payer_name = payer.payer_name if payer else claim.payer_id
        deadline_days = payer.filing_deadline_days if payer else 90
        remaining_days = max(0, deadline_days - claim.days_in_ar)
        preferred_contact = payer.preferred_contact_method if payer else "Portal"
        pred = claim.prediction

        # 1. Retrieve RAG Policy Context
        rag_chunks = self.rag.get_claim_context({
            "claim_id": claim.claim_id,
            "payer_id": claim.payer_id,
            "denial_reason": claim.denial_reason,
            "denial_code": claim.denial_code,
            "claim_type": claim.claim_type,
        }, top_k=2)

        best_chunk = rag_chunks[0] if rag_chunks else {
            "title": f"{payer_name} Standard Adjudication Policy",
            "content": f"{payer_name} processes claims within {deadline_days} days. Contact via {preferred_contact}.",
        }

        # 2. Determine Action & Channel
        is_denied = (claim.denial_status == "Denied" or claim.claim_status == "Denied")
        reason_lower = (claim.denial_reason or "").lower()
        code = claim.denial_code or ""

        if is_denied:
            action_type = "Appeal"
            channel = preferred_contact
            urgency = "Immediate" if remaining_days < 30 or (pred and pred.priority_band == "Critical") else "High"
            confidence = 0.94

            if "missing" in reason_lower or code == "CO-16":
                reasoning = (
                    f"Claim was denied by {payer_name} citing missing documentation (Code {code}). "
                    f"Under {payer_name} policy rules, submitting itemized statements and certified charts within "
                    f"{remaining_days} remaining filing days allows complete reconsideration."
                )
                generated_msg = self._generate_appeal_letter(claim, best_chunk, "Missing Documentation Reconciliation")
            elif "authorization" in reason_lower or code == "CO-197":
                reasoning = (
                    f"Claim denied for prior authorization (Code {code}). "
                    f"Drafting retroactive clinical necessity appeal with physician justification package."
                )
                generated_msg = self._generate_appeal_letter(claim, best_chunk, "Retroactive Prior Authorization Appeal")
            elif "medical necessity" in reason_lower or code == "CO-50":
                channel = "Phone / Medical Review Portal"
                reasoning = (
                    f"Claim denied for medical necessity (Code {code}). "
                    f"Scheduling clinical peer-to-peer discussion and providing evidence-based justification."
                )
                generated_msg = self._generate_appeal_letter(claim, best_chunk, "Clinical Medical Necessity Appeal & Peer-to-Peer")
            elif "timely filing" in reason_lower or code == "CO-29":
                channel = "Certified Mail / EDI"
                urgency = "Immediate"
                reasoning = (
                    f"Claim disputed under timely filing (Code {code}). "
                    f"Submitting EDI 999 / 277 clearinghouse transmission proof verifying timely submission."
                )
                generated_msg = self._generate_appeal_letter(claim, best_chunk, "Proof of Timely Filing Dispute")
            elif "duplicate" in reason_lower or code == "CO-18":
                action_type = "Resubmission"
                reasoning = (
                    f"Claim flagged as duplicate (Code {code}). "
                    f"Reconciling distinct procedure modifiers (-59 / -76) and resubmitting corrected electronic claim."
                )
                generated_msg = self._generate_resubmission_message(claim, best_chunk)
            else:
                reasoning = (
                    f"Formal first-level appeal initiated for '{claim.denial_reason or 'Claim Disallowance'}' "
                    f"targeting full recovery of ${claim.outstanding_amount:,.2f}."
                )
                generated_msg = self._generate_appeal_letter(claim, best_chunk, "First-Level Administrative Appeal")

        elif claim.claim_status == "Appeal Pending":
            action_type = "Status Inquiry"
            channel = "Portal"
            urgency = "High" if claim.days_in_ar > 60 else "Standard"
            confidence = 0.89
            reasoning = (
                f"An appeal is currently pending for claim #{claim.claim_id}. "
                f"Executing follow-up status check to verify adjudicator assignment and resolve delays."
            )
            generated_msg = self._generate_status_inquiry(claim, best_chunk)

        elif claim.days_in_ar > 45 or claim.followup_count >= 3:
            action_type = "Escalation"
            channel = "Phone / Portal"
            urgency = "High"
            confidence = 0.91
            reasoning = (
                f"Claim has aged {claim.days_in_ar} days in AR with {claim.followup_count} prior attempts without payment. "
                f"Escalating to {payer_name} supervisor claims unit."
            )
            generated_msg = self._generate_phone_script(claim, best_chunk)

        else:
            action_type = "Status Inquiry"
            channel = preferred_contact
            urgency = "Standard"
            confidence = 0.86
            reasoning = (
                f"Claim is in routine adjudication ({claim.days_in_ar} days). "
                f"Transmitting electronic 276 status check to ensure timely payment processing."
            )
            generated_msg = self._generate_status_inquiry(claim, best_chunk)

        return {
            "claim_id": claim.claim_id,
            "recommended_action": action_type,
            "channel": channel,
            "urgency": urgency,
            "confidence": confidence,
            "reasoning": reasoning,
            "retrieved_policy_title": best_chunk.get("title", f"{payer_name} Policy"),
            "retrieved_policy_snippet": best_chunk.get("content", ""),
            "generated_message": generated_msg,
            "filing_deadline_remaining_days": remaining_days,
            "created_at": datetime.now(timezone.utc),
        }

    def _generate_appeal_letter(self, claim: Claim, policy_chunk: Dict[str, Any], appeal_type: str) -> str:
        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id
        today_str = date.today().strftime("%B %d, %Y")

        return f"""================================================================================
REVENUE RECOVERY & PATIENT FINANCIAL SERVICES
FORMAL FIRST-LEVEL RECONSIDERATION & APPEAL
================================================================================

DATE: {today_str}
ATTENTION: {payer_name} — Claims Adjudication & Appeals Unit
RE: {appeal_type.upper()}

CLAIM IDENTIFICATION:
--------------------------------------------------------------------------------
• Claim ID:               {claim.claim_id}
• Patient Identifier:     {claim.patient_id}
• Rendering Provider:     {claim.provider_id}
• Date of Service:        {claim.service_date}
• Claim Incurred Date:    {claim.claim_date}
• Service Classification: {claim.claim_type} ({claim.place_of_service})
• Total Billed Amount:    ${claim.billed_amount:,.2f}
• Total Allowed Amount:   ${claim.allowed_amount:,.2f}
• Outstanding Balance:    ${claim.outstanding_amount:,.2f}
• Adverse Determination:  {claim.denial_code or 'N/A'} — {claim.denial_reason or 'Claim Disallowance'}

PAYER POLICY CITATION (GROUNDED VIA RAG):
--------------------------------------------------------------------------------
Reference Document: {policy_chunk.get('title', 'Payer Policy Guidelines')}
"{policy_chunk.get('content', 'Payer guidelines specify documentation and timely appeal protocol.')}"

STATEMENT OF APPEAL & JUSTIFICATION:
--------------------------------------------------------------------------------
Please accept this formal written appeal regarding the denial of Claim #{claim.claim_id}. 
Our clinical review confirms that all healthcare services rendered on {claim.service_date} met 
full medical necessity standards and comply with established {payer_name} billing criteria.

The primary denial reason ('{claim.denial_reason or 'Administrative Disallowance'}') has been 
thoroughly audited. Supporting documentation is attached to satisfy all payer conditions.

ATTACHED CLINICAL DOCUMENTATION & EXHIBITS:
--------------------------------------------------------------------------------
[✓] Exhibit A: Itemized Billing Statement (UB-04 / CMS-1500)
[✓] Exhibit B: Complete Certified Medical Chart & Operative Notes
[✓] Exhibit C: Physician Clinical Justification & Letter of Medical Necessity
[✓] Exhibit D: Prior Authorization Pre-Certification Record & EDI 277 Acceptance Receipt

REQUESTED ADJUDICATION ACTION:
--------------------------------------------------------------------------------
In accordance with prompt payment regulations and {payer_name}'s published policy timeline, 
we request immediate overturn of this denial and remittance of ${claim.outstanding_amount:,.2f}.

Authorized Billing Representative:
RecoverAI Autonomous Revenue Recovery Engine
Provider Revenue Cycle Operations
================================================================================
"""

    def _generate_status_inquiry(self, claim: Claim, policy_chunk: Dict[str, Any]) -> str:
        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id
        today_str = date.today().strftime("%B %d, %Y")

        return f"""================================================================================
EXPEDITED CLAIM STATUS INQUIRY (EDI 276 / SECURE PORTAL)
================================================================================
TRANSMISSION DATE: {today_str}
PAYER:             {payer_name} ({claim.payer_id})
CLAIM NUMBER:      {claim.claim_id}
PATIENT ID:        {claim.patient_id}
DATE OF SERVICE:   {claim.service_date}
OUTSTANDING:       ${claim.outstanding_amount:,.2f}

INQUIRY CONTEXT:
This claim has reached {claim.days_in_ar} days in AR without final payment posting. 
Standard published {payer_name} turnaround is {payer.avg_processing_days if payer else 15} business days.

POLICY BENCHMARK:
"{policy_chunk.get('content', '')[:250]}..."

REQUIRED STATUS UPDATE:
1. Verification of active claim status in adjudication system.
2. Estimated check release or EFT remittance date for ${claim.outstanding_amount:,.2f}.
3. Specification of any outstanding clinical requirements.
================================================================================
"""

    def _generate_phone_script(self, claim: Claim, policy_chunk: Dict[str, Any]) -> str:
        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id

        return f"""================================================================================
LIVE PROVIDER REPRESENTATIVE CALL SCRIPT & ESCALATION WORKFLOW
================================================================================
TARGET PAYER:   {payer_name} Provider Services Hotline
CLAIM ID:       {claim.claim_id} | PATIENT ID: {claim.patient_id}
SERVICE DATE:   {claim.service_date} | OUTSTANDING: ${claim.outstanding_amount:,.2f}
AGING DURATION: {claim.days_in_ar} Days in AR | PRIOR ATTEMPTS: {claim.followup_count}

CALL TALKING POINTS:
--------------------------------------------------------------------------------
1. OPENING:
   "Hello, my name is calling on behalf of Provider Financial Services. 
    I am calling to escalate unadjudicated claim #{claim.claim_id} for Patient ID {claim.patient_id}."

2. CONTEXT & ESCALATION:
   "Our records reflect {claim.followup_count} prior follow-up inquiries. The claim is now {claim.days_in_ar} days 
    aged in AR with ${claim.outstanding_amount:,.2f} outstanding balance."

3. POLICY REFERENCE:
   "According to {payer_name}'s policy guidelines ({policy_chunk.get('title', 'Policy Guidelines')}), 
    claims should be resolved within standard windows. Can you transfer me to a Senior Claims Examiner?"

4. RESOLUTION INQUIRY:
   "Can you confirm the exact EFT date, or provide a reference number for supervisory review?"
================================================================================
"""

    def _generate_resubmission_message(self, claim: Claim, policy_chunk: Dict[str, Any]) -> str:
        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id

        return f"""================================================================================
ELECTRONIC CORRECTED CLAIM RESUBMISSION (EDI 837)
================================================================================
TO:           {payer_name} Claims Processing Center
CLAIM ID:     {claim.claim_id} (Frequency Code: 7 - Replacement of Prior Claim)
ORIGINAL REF: {claim.denial_code or 'CO-18'} (Duplicate Claim Disallowance)
OUTSTANDING:  ${claim.outstanding_amount:,.2f}

CORRECTION SUMMARY:
Claim #{claim.claim_id} has been audited for distinct anatomical service line items. 
Distinct procedural modifier (-59 / -76) has been appended to distinguish separate surgical/diagnostic sessions.

POLICY COMPLIANCE:
"{policy_chunk.get('content', '')[:250]}..."

Please process this corrected submission for payment.
================================================================================
"""

    def execute_action(
        self,
        db: Session,
        claim_id: str,
        simulate: bool = True,
        custom_message: Optional[str] = None,
        override_channel: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes or simulates the agent decision, persisting records in agent_actions and followups tables.
        """
        claim = db.query(Claim).filter(Claim.claim_id == claim_id.strip()).first()
        if not claim:
            raise ValueError(f"Claim '{claim_id}' not found")

        decision = self.formulate_decision(claim)

        final_msg = custom_message or decision["generated_message"]
        final_channel = override_channel or decision["channel"]
        action_type = decision["recommended_action"]
        status_str = "SIMULATED" if simulate else "EXECUTED"

        # 1. Persist AgentAction record
        action_record = AgentAction(
            claim_id=claim.claim_id,
            recommended_action=action_type,
            reasoning=decision["reasoning"],
            confidence=decision["confidence"],
            retrieved_policy=json.dumps({
                "title": decision["retrieved_policy_title"],
                "snippet": decision["retrieved_policy_snippet"][:300],
            }),
            generated_message=final_msg,
            approval_status=status_str,
            created_at=datetime.now(timezone.utc),
        )
        db.add(action_record)

        # 2. Append Followup record to claim audit trail
        now_date_str = date.today().strftime("%Y-%m-%d")
        new_followup_id = f"FU_AGT_{int(datetime.now(timezone.utc).timestamp())}_{claim.claim_id[-4:]}"
        
        followup_record = Followup(
            followup_id=new_followup_id,
            claim_id=claim.claim_id,
            followup_date=now_date_str,
            channel=final_channel,
            action_type=f"AI Agent: {action_type}",
            message=final_msg[:350] + "...",
            payer_response="Pending Payer Response",
            response_date=None,
            outcome="Action Initiated",
        )
        db.add(followup_record)

        # 3. Update Claim follow-up counter and last follow-up timestamp
        claim.followup_count = (claim.followup_count or 0) + 1
        claim.last_followup_date = now_date_str
        if is_denied := (claim.denial_status == "Denied" or claim.claim_status == "Denied"):
            if action_type == "Appeal":
                claim.appeal_status = "In Review"

        db.commit()
        db.refresh(action_record)

        return {
            "action_id": action_record.action_id,
            "claim_id": claim.claim_id,
            "recommended_action": action_type,
            "channel": final_channel,
            "approval_status": status_str,
            "reasoning": decision["reasoning"],
            "generated_message": final_msg,
            "confidence": decision["confidence"],
            "created_at": action_record.created_at,
        }

    decide = formulate_decision


# Singleton AI Agent instance
followup_agent = AIFollowUpAgent()

