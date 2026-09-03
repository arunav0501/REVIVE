"""
AR Follow-Up AI - Payer Response Simulator (Phase 11)

Simulates realistic, probabilistic payer adjudication responses based on:
- Claim clinical state (Denial reason, Code, Outstanding balance, Days in AR)
- Payer policy profile (Filing limits, processing turnaround)
- ML Model recovery probabilities
- Follow-up action type & quality (Appeal, Inquiry, Resubmission, Escalation)

Generates:
1. Outcome Determination: APPROVED_FULL, APPROVED_PARTIAL, ADDITIONAL_INFO_REQUIRED, DENIAL_UPHELD
2. Realistic Remittance Advice / Portal Response Texts with EFT reference numbers
3. Real-time DB state updates (when requested)
"""

from typing import Dict, Any, Optional, List
from datetime import date, timedelta
import random
import numpy as np
from sqlalchemy.orm import Session

from backend.app.models import Claim, Followup, ClaimOutcome, Payer


class PayerResponseSimulator:
    def __init__(self):
        pass

    def calculate_probability_distribution(
        self,
        claim: Claim,
        action_type: str = "Appeal",
        action_quality: str = "high",
    ) -> Dict[str, float]:
        """
        Calculates realistic 4-class outcome probability distribution based on
        ML recovery probability, claim denial state, payer profile, and action quality.
        """
        pred = claim.prediction
        base_recovery = float(pred.recovery_probability) if pred else 0.55
        denial_prob = float(pred.denial_probability) if pred else 0.45

        payer = claim.payer
        deadline_days = payer.filing_deadline_days if payer else 90
        remaining_days = max(0, deadline_days - claim.days_in_ar)

        # Quality modifier
        q_mod = 0.15 if action_quality == "high" else (-0.15 if action_quality == "low" else 0.0)

        # Action-scenario synergy modifier
        act_lower = action_type.lower().strip()
        code = (claim.denial_code or "").upper()
        reason = (claim.denial_reason or "").lower()

        syn_mod = 0.0
        if "appeal" in act_lower and ("co-16" in code or "missing" in reason or "co-197" in code or "auth" in reason):
            syn_mod += 0.12
        elif "resubmission" in act_lower and ("co-18" in code or "duplicate" in reason):
            syn_mod += 0.18
        elif "escalation" in act_lower and claim.followup_count >= 3:
            syn_mod += 0.10

        # Expired deadline penalty
        if remaining_days == 0:
            syn_mod -= 0.25

        effective_rec = np.clip(base_recovery + q_mod + syn_mod, 0.05, 0.95)

        # Distribution allocation
        p_approved_full = round(float(effective_rec * 0.65), 4)
        p_approved_partial = round(float(effective_rec * 0.35), 4)
        
        remaining_mass = max(0.05, 1.0 - (p_approved_full + p_approved_partial))
        p_need_info = round(float(remaining_mass * (0.60 if "co-16" in code else 0.40)), 4)
        p_denied = round(float(max(0.02, 1.0 - (p_approved_full + p_approved_partial + p_need_info))), 4)

        # Normalize to sum exactly to 1.0
        total = p_approved_full + p_approved_partial + p_need_info + p_denied
        p_approved_full = round(p_approved_full / total, 4)
        p_approved_partial = round(p_approved_partial / total, 4)
        p_need_info = round(p_need_info / total, 4)
        p_denied = round(1.0 - (p_approved_full + p_approved_partial + p_need_info), 4)

        return {
            "p_approved_full": p_approved_full,
            "p_approved_partial": p_approved_partial,
            "p_additional_info_required": p_need_info,
            "p_denial_upheld": p_denied,
        }

    def simulate_response(
        self,
        claim: Claim,
        action_type: str = "Appeal",
        channel: str = "Portal",
        action_quality: str = "high",
        apply_to_db: bool = False,
        db: Optional[Session] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Simulates realistic payer outcome, calculates recovered amount, generates response remittance text,
        and optionally updates the SQLite database.
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        probs = self.calculate_probability_distribution(claim, action_type, action_quality)

        outcomes = ["APPROVED_FULL", "APPROVED_PARTIAL", "ADDITIONAL_INFO_REQUIRED", "DENIAL_UPHELD"]
        weights = [
            probs["p_approved_full"],
            probs["p_approved_partial"],
            probs["p_additional_info_required"],
            probs["p_denial_upheld"],
        ]

        sampled_outcome = random.choices(outcomes, weights=weights, k=1)[0]

        payer = claim.payer
        payer_name = payer.payer_name if payer else claim.payer_id
        orig_outstanding = float(claim.outstanding_amount)
        turnaround = (payer.avg_response_days if payer else 7) + random.randint(-1, 3)
        turnaround = max(2, turnaround)
        sim_response_date = (date.today() + timedelta(days=turnaround)).strftime("%Y-%m-%d")

        remit_ref = f"EFT-{payer.payer_id if payer else 'PAY'}-{random.randint(100000, 999999)}"

        if sampled_outcome == "APPROVED_FULL":
            recovered_amount = orig_outstanding
            remaining_outstanding = 0.0
            new_claim_status = "Paid"
            payer_response_text = (
                f"Adjudication Decision: RECONSIDERATION APPROVED IN FULL. "
                f"Adverse determination overturned following review of clinical documentation. "
                f"Remittance of ${recovered_amount:,.2f} released via Electronic Funds Transfer ({remit_ref}). "
                f"Transaction finalized by {payer_name} Claims Operations."
            )
        elif sampled_outcome == "APPROVED_PARTIAL":
            # 65% to 88% partial recovery
            pct = random.uniform(0.65, 0.88)
            recovered_amount = round(orig_outstanding * pct, 2)
            remaining_outstanding = round(orig_outstanding - recovered_amount, 2)
            new_claim_status = "Paid"
            payer_response_text = (
                f"Adjudication Decision: PARTIAL PAYMENT APPROVED. "
                f"Claim re-adjudicated per contracted fee schedule allowances. "
                f"Approved payment: ${recovered_amount:,.2f} ({pct*100:.1f}% of disputed balance). "
                f"Remaining balance of ${remaining_outstanding:,.2f} categorized under contractual adjustment. "
                f"Remittance Ref: {remit_ref}."
            )
        elif sampled_outcome == "ADDITIONAL_INFO_REQUIRED":
            recovered_amount = 0.0
            remaining_outstanding = orig_outstanding
            new_claim_status = "In Review"
            payer_response_text = (
                f"Adjudication Status: ADDITIONAL INFORMATION REQUIRED. "
                f"First-level appeal received and logged under inquiry tracking #{remit_ref}. "
                f"Adjudication is suspended pending submission of itemized procedure breakdown and signed physician operative note. "
                f"Please submit requested documentation within 30 days via {channel}."
            )
        else:  # DENIAL_UPHELD
            recovered_amount = 0.0
            remaining_outstanding = orig_outstanding
            new_claim_status = "Denied"
            payer_response_text = (
                f"Adjudication Decision: DENIAL UPHELD. "
                f"Review of claim #{claim.claim_id} confirmed original adverse determination citing "
                f"'{claim.denial_reason or 'Contractual Policy Criteria'}' (Code {claim.denial_code or 'CO-45'}). "
                f"Provider has 60 calendar days to file a Level-2 External Grievance. Ref: {remit_ref}."
            )

        # Apply changes to DB if requested
        if apply_to_db and db is not None:
            claim.claim_status = new_claim_status
            if recovered_amount > 0:
                claim.paid_amount = round(float(claim.paid_amount or 0.0) + recovered_amount, 2)
                claim.outstanding_amount = remaining_outstanding
            
            # Append follow-up response
            fu_id = f"FU_SIM_{random.randint(10000, 99999)}_{claim.claim_id[-4:]}"
            new_fu = Followup(
                followup_id=fu_id,
                claim_id=claim.claim_id,
                followup_date=date.today().strftime("%Y-%m-%d"),
                channel=channel,
                action_type=f"Payer Response ({action_type})",
                message=f"Follow-up submitted via {channel}.",
                payer_response=payer_response_text[:350],
                response_date=sim_response_date,
                outcome="Positive" if recovered_amount > 0 else ("Action Required" if sampled_outcome == "ADDITIONAL_INFO_REQUIRED" else "Negative"),
            )
            db.add(new_fu)

            # Update outcome record
            outcome_rec = db.query(ClaimOutcome).filter(ClaimOutcome.claim_id == claim.claim_id).first()
            if outcome_rec and recovered_amount > 0:
                outcome_rec.recovered_amount = round(float(outcome_rec.recovered_amount or 0.0) + recovered_amount, 2)
                outcome_rec.successful_followup = 1
                if remaining_outstanding == 0:
                    outcome_rec.final_outcome = "Paid"

            db.commit()

        return {
            "claim_id": claim.claim_id,
            "payer_id": claim.payer_id,
            "payer_name": payer_name,
            "action_type": action_type,
            "channel": channel,
            "simulated_outcome": sampled_outcome,
            "recovered_amount": recovered_amount,
            "original_outstanding": orig_outstanding,
            "remaining_outstanding": remaining_outstanding,
            "new_claim_status": new_claim_status,
            "turnaround_days": turnaround,
            "simulated_response_date": sim_response_date,
            "payer_response_text": payer_response_text,
            "remittance_reference": remit_ref,
            "probability_distribution": probs,
            "applied_to_db": apply_to_db,
        }


# Singleton simulator instance
payer_simulator = PayerResponseSimulator()
