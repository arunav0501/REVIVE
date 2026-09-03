"""
AR Follow-Up AI - Closed-Loop Autonomous Recovery Engine (Phase 12)

Automates the complete revenue recovery lifecycle:
1. Ingestion: Pick high-priority unrecovered claims
2. AI Decision: Determine optimal strategy + retrieve RAG policy
3. Generator: Synthesize customized, grounded communication artifacts
4. Simulator: Probabilistic payer adjudication simulation
5. Ledger State: Update claim statuses, balances, and followup records
6. Outcomes: Record recovered revenues in database
7. Analytics: Recompute portfolio financial yield and metrics
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func


from backend.app.models import Claim, Prediction, AgentAction, Followup, ClaimOutcome
from backend.app.agent.followup_agent import followup_agent
from backend.app.generator.artifact_generator import artifact_generator
from backend.app.simulator.payer_simulator import payer_simulator


class ClosedLoopRecoveryEngine:
    def __init__(self):
        self.agent = followup_agent
        self.generator = artifact_generator
        self.simulator = payer_simulator

    def run_autonomous_loop(
        self,
        db: Session,
        batch_size: int = 10,
        min_priority_band: str = "High",
        payer_id: Optional[str] = None,
        action_quality: str = "high",
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end closed loop recovery cycle on top prioritized claims.
        """
        batch_size = max(1, min(50, batch_size))
        run_id = f"RUN_{uuid.uuid4().hex[:8].upper()}"
        start_time = datetime.now(timezone.utc).isoformat()


        # 1. Select High-Priority Unresolved Claims
        query = (
            db.query(Claim)
            .join(Prediction, Claim.claim_id == Prediction.claim_id)
            .filter(Claim.outstanding_amount > 0)
            .filter(Claim.claim_status.notin_(["Paid"]))
        )

        if payer_id:
            query = query.filter(Claim.payer_id == payer_id.strip())

        band_filter = min_priority_band.lower().strip()
        if band_filter == "critical":
            query = query.filter(Prediction.priority_band == "Critical")
        elif band_filter == "high":
            query = query.filter(Prediction.priority_band.in_(["Critical", "High"]))
        elif band_filter == "medium":
            query = query.filter(Prediction.priority_band.in_(["Critical", "High", "Medium"]))

        candidates = query.order_by(Prediction.priority_score.desc()).limit(batch_size).all()

        results: List[Dict[str, Any]] = []
        total_orig_outstanding = 0.0
        total_recovered = 0.0
        outcomes_breakdown: Dict[str, int] = {
            "APPROVED_FULL": 0,
            "APPROVED_PARTIAL": 0,
            "ADDITIONAL_INFO_REQUIRED": 0,
            "DENIAL_UPHELD": 0,
        }
        actions_breakdown: Dict[str, int] = {}

        for claim in candidates:
            orig_outstanding = float(claim.outstanding_amount)
            total_orig_outstanding += orig_outstanding
            initial_status = claim.claim_status

            # Step 2: Formulate Decision
            decision = self.agent.formulate_decision(claim)
            chosen_action = decision["recommended_action"]

            chosen_channel = decision["channel"]
            actions_breakdown[chosen_action] = actions_breakdown.get(chosen_action, 0) + 1

            # Step 3: Generate Communication Artifact
            artifacts = self.generator.generate(
                claim=claim,
                artifact_type="all",
                tone="urgent",
            )
            msg_draft = artifacts.get("appeal_letter") or decision.get("generated_message") or ""

            # Step 4: Simulate Payer Response & Apply DB State Updates
            sim = self.simulator.simulate_response(
                claim=claim,
                action_type=chosen_action,
                channel=chosen_channel,
                action_quality=action_quality,
                apply_to_db=True,
                db=db,
            )

            rec_amount = sim["recovered_amount"]
            total_recovered += rec_amount
            sim_outcome = sim["simulated_outcome"]
            outcomes_breakdown[sim_outcome] = outcomes_breakdown.get(sim_outcome, 0) + 1

            # Step 5: Log Agent Action
            agent_log = AgentAction(
                claim_id=claim.claim_id,
                recommended_action=chosen_action,
                reasoning=decision["reasoning"],
                confidence=decision["confidence"],
                retrieved_policy=str(decision.get("retrieved_policy_snippet", "")),
                generated_message=msg_draft,
                approval_status="EXECUTED",
                created_at=datetime.now(timezone.utc),
            )

            db.add(agent_log)
            db.commit()

            results.append({
                "claim_id": claim.claim_id,
                "patient_id": claim.patient_id,
                "payer_id": claim.payer_id,
                "payer_name": claim.payer.payer_name if claim.payer else claim.payer_id,
                "priority_score": float(claim.prediction.priority_score) if claim.prediction else 0.0,
                "priority_band": claim.prediction.priority_band if claim.prediction else "Low",
                "initial_status": initial_status,
                "chosen_action": chosen_action,
                "chosen_channel": chosen_channel,
                "grounded_policy_title": decision.get("retrieved_policy_title", "Payer Policy"),
                "simulated_outcome": sim_outcome,
                "original_outstanding": orig_outstanding,
                "recovered_amount": rec_amount,
                "final_outstanding": sim["remaining_outstanding"],
                "final_status": sim["new_claim_status"],
                "payer_response_snippet": sim["payer_response_text"][:140] + "...",
                "remittance_reference": sim["remittance_reference"],
            })

        # Step 6: Recompute System Metrics
        curr_total_ar = float(db.query(func.sum(Claim.outstanding_amount)).scalar() or 0.0)
        curr_total_recovered = float(db.query(func.sum(ClaimOutcome.recovered_amount)).scalar() or 0.0)
        yield_pct = round((total_recovered / total_orig_outstanding * 100), 2) if total_orig_outstanding > 0 else 0.0

        return {
            "run_id": run_id,
            "timestamp": start_time,
            "batch_size": len(candidates),
            "total_processed": len(candidates),
            "total_original_outstanding": round(total_orig_outstanding, 2),
            "total_recovered": round(total_recovered, 2),
            "recovery_yield_percentage": yield_pct,
            "outcomes_breakdown": outcomes_breakdown,
            "actions_breakdown": actions_breakdown,
            "updated_dashboard_total_ar": round(curr_total_ar, 2),
            "updated_dashboard_recovered_revenue": round(curr_total_recovered, 2),
            "results": results,
        }


# Singleton engine instance
closed_loop_engine = ClosedLoopRecoveryEngine()
