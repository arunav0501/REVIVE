"""
AR Follow-Up AI - Multi-Format Follow-Up Generator (Phase 10)

Generates clean, professional markdown/text artifacts grounded in claim data and RAG policy rules:
1. Formal CMS/UB-04 Appeal Letters
2. Payer Portal Messages (Availity / NaviNet / Optum / Change Healthcare)
3. Call Center Phone Scripts with Escalation Pathways
4. Secure Email Templates
5. Electronic Resubmission Notes (EDI 837)
"""

from typing import Dict, Any, Optional
from datetime import date
from backend.app.models import Claim
from backend.app.rag.engine import rag_engine


class FollowUpArtifactGenerator:
    def __init__(self):
        self.rag = rag_engine

    def generate(
        self,
        claim: Claim,
        artifact_type: str = "all",
        tone: str = "firm",
        custom_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates requested artifacts grounded in claim clinical metadata and RAG policy rules.
        """
        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id
        deadline_days = payer.filing_deadline_days if payer else 90
        remaining_days = max(0, deadline_days - claim.days_in_ar)

        # Retrieve Grounded Policy Context via RAG
        rag_chunks = self.rag.get_claim_context({
            "claim_id": claim.claim_id,
            "payer_id": claim.payer_id,
            "denial_reason": claim.denial_reason,
            "denial_code": claim.denial_code,
            "claim_type": claim.claim_type,
        }, top_k=2)

        best_chunk = rag_chunks[0] if rag_chunks else {
            "title": f"{payer_name} Standard Policy",
            "content": f"{payer_name} standard processing timeframe is {deadline_days} days.",
            "required_documents": "Itemized statement;Medical records",
        }

        response = {
            "claim_id": claim.claim_id,
            "patient_id": claim.patient_id,
            "provider_id": claim.provider_id,
            "payer_name": payer_name,
            "payer_id": claim.payer_id,
            "denial_code": claim.denial_code,
            "denial_reason": claim.denial_reason,
            "outstanding_amount": claim.outstanding_amount,
            "grounded_policy_title": best_chunk.get("title", f"{payer_name} Policy"),
            "grounded_policy_content": best_chunk.get("content", ""),
            "appeal_letter": None,
            "portal_message": None,
            "phone_script": None,
            "email_template": None,
            "edi_resubmission_note": None,
        }

        art_lower = artifact_type.lower().strip()

        if art_lower in ["all", "appeal_letter", "appeal"]:
            response["appeal_letter"] = self._build_appeal_letter(claim, best_chunk, tone, remaining_days, custom_notes)

        if art_lower in ["all", "portal_message", "portal"]:
            response["portal_message"] = self._build_portal_message(claim, best_chunk, tone, remaining_days, custom_notes)

        if art_lower in ["all", "phone_script", "phone", "call"]:
            response["phone_script"] = self._build_phone_script(claim, best_chunk, tone, remaining_days, custom_notes)

        if art_lower in ["all", "email_template", "email"]:
            response["email_template"] = self._build_email_template(claim, best_chunk, tone, remaining_days, custom_notes)

        if art_lower in ["all", "edi_resubmission_note", "edi", "resubmission"]:
            response["edi_resubmission_note"] = self._build_edi_note(claim, best_chunk, tone, remaining_days, custom_notes)

        return response

    def _build_appeal_letter(
        self,
        claim: Claim,
        policy: Dict[str, Any],
        tone: str,
        remaining_days: int,
        custom_notes: Optional[str] = None,
    ) -> str:
        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id
        today_str = date.today().strftime("%B %d, %Y")
        code = claim.denial_code or "N/A"
        reason = claim.denial_reason or "Claim Disallowance"

        urgency_note = ""
        if tone == "urgent" or remaining_days <= 30:
            urgency_note = f"\n*** EXPEDITED REVIEW REQUESTED — {remaining_days} DAYS REMAINING BEFORE TIMELY FILING FORFEITURE ***\n"

        denial_specific_text = self._get_denial_justification(code, reason, claim)

        return f"""================================================================================
REVENUE RECOVERY & PATIENT FINANCIAL SERVICES
FORMAL FIRST-LEVEL RECONSIDERATION & APPEAL
================================================================================
DATE:                  {today_str}
ATTENTION:             {payer_name} — Claims Adjudication & Appeals Unit
ADDRESS:               Provider Appeals Department
ELECTRONIC SUBMISSION: Secure Provider Portal / Clearinghouse
{urgency_note}
SUBJECT: FORMAL APPEAL REGARDING CLAIM #{claim.claim_id}
--------------------------------------------------------------------------------

CLAIM IDENTIFICATION DATA:
--------------------------------------------------------------------------------
• Claim Identification:     {claim.claim_id}
• Patient Identifier:        {claim.patient_id}
• Rendering Provider:        {claim.provider_id}
• Date of Service (DOS):     {claim.service_date}
• Claim Incurred Date:       {claim.claim_date}
• Service Classification:    {claim.claim_type} ({claim.place_of_service})
• Total Billed Charges:      ${claim.billed_amount:,.2f}
• Total Allowed Charges:     ${claim.allowed_amount:,.2f}
• Current Outstanding:       ${claim.outstanding_amount:,.2f}
• Denial Reason / Code:      {code} — {reason}

PAYER POLICY GROUNDING (RETRIEVED VIA RAG):
--------------------------------------------------------------------------------
Reference Document: {policy.get('title', 'Payer Policy Rules')}
"{policy.get('content', 'Standard claim adjudication and appeal filing guidelines.')}"

CLINICAL & ADMINISTRATIVE DISPUTE JUSTIFICATION:
--------------------------------------------------------------------------------
Please accept this correspondence as our formal first-level appeal of the adverse 
determination rendered against Claim #{claim.claim_id}. All healthcare services 
rendered on {claim.service_date} met established medical necessity criteria and complied 
with published {payer_name} billing guidelines.

{denial_specific_text}

{f"ADDITIONAL CLINICAL NOTES: {custom_notes}" if custom_notes else ""}

ATTACHED VERIFICATION EXHIBITS:
--------------------------------------------------------------------------------
[✓] Exhibit A: Itemized Billing Statement and UB-04 / CMS-1500 Form
[✓] Exhibit B: Complete Certified Medical Chart Notes and Operative Report
[✓] Exhibit C: Letter of Clinical Justification from Attending Physician
[✓] Exhibit D: Proof of Prior Authorization Certification & EDI Acceptance Receipt

DEMAND FOR REMITTANCE:
--------------------------------------------------------------------------------
Pursuant to prompt payment regulations, please re-adjudicate Claim #{claim.claim_id} 
and issue payment in the amount of ${claim.outstanding_amount:,.2f}.

Sincerely,

Revenue Cycle Management Operations
RecoverAI Autonomous Recovery Platform
================================================================================
"""

    def _build_portal_message(
        self,
        claim: Claim,
        policy: Dict[str, Any],
        tone: str,
        remaining_days: int,
        custom_notes: Optional[str] = None,
    ) -> str:
        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id
        code = claim.denial_code or "N/A"
        reason = claim.denial_reason or "Under Review"

        return f"""================================================================================
SECURE PROVIDER PORTAL INQUIRY TRANSMISSION
================================================================================
PAYER PORTAL:          {payer_name} Provider Online Services
INQUIRY CATEGORY:      Claims Status & Reconsideration
CLAIM REFERENCE:       {claim.claim_id}
PATIENT ID:            {claim.patient_id}
DATE OF SERVICE:       {claim.service_date}
OUTSTANDING AMOUNT:    ${claim.outstanding_amount:,.2f}
ADJUDICATION STATUS:   {claim.claim_status} (Denial: {code} - {reason})

MESSAGE BODY:
--------------------------------------------------------------------------------
We are submitting an inquiry regarding Claim #{claim.claim_id} (DOS: {claim.service_date}) 
which is currently {claim.days_in_ar} days aged in AR. 

Under {payer_name}'s policy guidelines ("{policy.get('title', 'Payer Policy')}"), the standard 
processing turnaround is {payer.avg_processing_days if payer else 15} days. 

{f"Note: {custom_notes}" if custom_notes else "Please verify whether all required attachments have been received and confirm the scheduled EFT release date."}

REQUIRED RESOLUTION:
1. Reopen and reprocess Claim #{claim.claim_id} for ${claim.outstanding_amount:,.2f}.
2. Provide direct confirmation reference number within 5 business days.
================================================================================
"""

    def _build_phone_script(
        self,
        claim: Claim,
        policy: Dict[str, Any],
        tone: str,
        remaining_days: int,
        custom_notes: Optional[str] = None,
    ) -> str:
        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id
        code = claim.denial_code or "N/A"

        return f"""================================================================================
CALL CENTER AGENT PHONE SCRIPT & ESCALATION WORKFLOW
================================================================================
TARGET PAYER:          {payer_name} Provider Services (Toll-Free Claims Line)
CLAIM ID:              {claim.claim_id} | PATIENT ID: {claim.patient_id}
DATE OF SERVICE:       {claim.service_date} | OUTSTANDING: ${claim.outstanding_amount:,.2f}
CURRENT AR AGING:      {claim.days_in_ar} Days in AR ({remaining_days} Days Remaining)
PRIOR FOLLOW-UPS:      {claim.followup_count} Recorded Inquiries

STEP-BY-STEP DIALOGUE & TALKING POINTS:
--------------------------------------------------------------------------------
1. CALL INITIATION:
   "Hello, my name is calling from Provider Revenue Operations. 
    I am calling to check the status and request adjudication of claim #{claim.claim_id} 
    for patient {claim.patient_id}, date of service {claim.service_date}."

2. CLAIM VERIFICATION:
   "Can you verify that claim #{claim.claim_id} with billed amount ${claim.billed_amount:,.2f} 
    is on file in your active adjudication system?"

3. CHALLENGING DENIAL / DELAY:
   "Our records reflect that this claim has been outstanding for {claim.days_in_ar} days. 
    Regarding denial code {code}: our clinical documentation confirms full medical necessity."

4. POLICY CITATION:
   "Under {payer_name}'s published guidelines ({policy.get('title', 'Policy Guidelines')}), 
    claims should be resolved within standard processing windows."

5. SUPERVISORY ESCALATION:
   "Since this claim has {claim.followup_count} prior attempts without resolution, please transfer 
    me to a Senior Claims Examiner or Supervisor."

6. DOCUMENTATION OF CALL:
   • Representative Name & ID: ______________________
   • Call Reference Number:    ______________________
   • Promised Action & Date:   ______________________
================================================================================
"""

    def _build_email_template(
        self,
        claim: Claim,
        policy: Dict[str, Any],
        tone: str,
        remaining_days: int,
        custom_notes: Optional[str] = None,
    ) -> str:
        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id
        code = claim.denial_code or "N/A"
        reason = claim.denial_reason or "Adjudication Delay"

        return f"""================================================================================
SECURE HIPAA-COMPLIANT EMAIL TEMPLATE
================================================================================
TO:                    appeals-review@{payer_name.lower().replace(' ', '')}.com
SUBJECT:               URGENT APPEAL: Claim #{claim.claim_id} | Patient ID: {claim.patient_id} | DOS: {claim.service_date}
ATTACHMENTS:           Claim_{claim.claim_id}_Medical_Records.pdf, Itemized_Bill.pdf

Dear {payer_name} Claims and Appeals Committee,

This email serves as our formal written request for review and reconsideration of Claim #{claim.claim_id}, 
rendered for Patient {claim.patient_id} on {claim.service_date}.

CLAIM SUMMARY:
• Claim Number:        {claim.claim_id}
• Rendering Provider:  {claim.provider_id}
• Total Billed:        ${claim.billed_amount:,.2f}
• Outstanding Balance: ${claim.outstanding_amount:,.2f}
• Denial Reason:       {code} — {reason}
• Current AR Duration: {claim.days_in_ar} Days ({remaining_days} Days Remaining)

POLICY COMPLIANCE:
In reference to {payer_name}'s policy document ("{policy.get('title', 'Payer Policy')}"), 
all required clinical charts and diagnostic records are attached to this transmission.

{f"Additional Remarks: {custom_notes}" if custom_notes else "Please reply with confirmation of receipt and the assigned appeal tracking number."}

Respectfully submitted,

Provider Revenue Recovery Operations
RecoverAI Automated AR System
================================================================================
"""

    def _build_edi_note(
        self,
        claim: Claim,
        policy: Dict[str, Any],
        tone: str,
        remaining_days: int,
        custom_notes: Optional[str] = None,
    ) -> str:
        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id

        return f"""================================================================================
ELECTRONIC RESUBMISSION PACKET (EDI 837 / 277)
================================================================================
TRANSACTION:           ANSI ASC X12 837 Health Care Claim (Professional / Institutional)
PAYER NAME & ID:       {payer_name} ({claim.payer_id})
CLAIM CONTROL NUMBER:  {claim.claim_id}
CLAIM FREQUENCY CODE:  7 (Replacement of Prior Claim)
ORIGINAL REF NUM:      {claim.claim_id}-ORIG
TOTAL AMOUNT:          ${claim.outstanding_amount:,.2f}

SEGMENT MODIFICATIONS:
• Loop 2300 (Claim Info): CLM*{claim.claim_id}*{claim.outstanding_amount:,.2f}***11::1*Y*A*Y*Y
• Loop 2300 (PWK Segment): PWK*09*AA***AC*{claim.claim_id}_CLINICAL_DOCS
• Loop 2400 (Service Line): SV1*HC:99214:25*{claim.outstanding_amount:,.2f}*UN*1***1

AUDIT JUSTIFICATION:
Corrected claim resubmission addressing {claim.denial_code or 'CO-18'} disallowance. 
Grounding: {policy.get('title', 'Payer EDI Policy')}.
================================================================================
"""

    def _get_denial_justification(self, code: str, reason: str, claim: Claim) -> str:
        code_upper = code.upper().strip()
        if "16" in code_upper or "missing" in reason.lower():
            return (
                "The claim was disallowed under Denial Code CO-16 citing missing information. "
                "Enclosed herein please find the complete, itemized medical billing statement, certified operative report, "
                "and physician progress notes which provide full clinical documentation satisfying all coding specifications."
            )
        elif "197" in code_upper or "authorization" in reason.lower():
            return (
                "The claim was disallowed under Denial Code CO-197 for prior authorization. "
                "The accompanying exhibits establish that the surgical/diagnostic intervention was medically urgent and "
                "eligible for retroactive pre-certification. Attached is the physician's urgent necessity certification."
            )
        elif "50" in code_upper or "medical necessity" in reason.lower():
            return (
                "The claim was disallowed under Denial Code CO-50 asserting non-covered or medically unnecessary care. "
                "Comprehensive diagnostic charts and peer-reviewed treatment guidelines are attached demonstrating that "
                "conservative therapies had been exhausted and the rendered care was essential to patient recovery."
            )
        elif "29" in code_upper or "timely filing" in reason.lower():
            return (
                "The claim was disallowed under Denial Code CO-29 citing expired timely filing limits. "
                "Attached as Exhibit D is our electronic clearinghouse EDI 999/277 timestamped acknowledgment proving initial "
                "transmission occurred within the allowable timely filing window."
            )
        elif "18" in code_upper or "duplicate" in reason.lower():
            return (
                "The claim was disallowed under Denial Code CO-18 as a duplicate service. "
                "Our billing audit verifies that distinct procedural modifiers were performed across separate anatomical sites "
                "during distinct clinical sessions. An updated replacement claim has been compiled."
            )
        else:
            return (
                f"The claim was disallowed citing '{reason}' (Code {code}). "
                f"Our clinical and financial audit confirms complete compliance with billing regulations and requests full reimbursement."
            )


# Singleton generator instance
artifact_generator = FollowUpArtifactGenerator()
