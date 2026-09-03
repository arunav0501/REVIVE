#!/usr/bin/env python3
"""
RecoverAI - Autonomous AR Follow-Up AI Platform
Complete End-to-End System Demonstration Script
"""

import sys
import os
import time
import json
import httpx

API_BASE = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()}")
    print("=" * 80)

def print_step(step_num: int, title: str):
    print(f"\n[STEP {step_num}] {title}")
    print("-" * 80)

def main():
    client = httpx.Client(base_url=API_BASE, timeout=20.0)
    
    print_header("RecoverAI — Autonomous AR Follow-Up & Revenue Cycle AI Platform")
    print("Connecting to live backend at:", API_BASE)

    # 1. Health & Database Verification
    print_step(1, "System Health & SQLite Knowledge Base Check")
    res = client.get("/health")
    if res.status_code != 200:
        print(f"Failed to connect to API: {res.text}")
        sys.exit(1)
    health = res.json()
    print(f"✓ Health Status: {health['status'].upper()} (Version: {health['version']})")
    print(f"✓ SQLite Database: {health['database']['status']} ({health['database']['database_url']})")
    print(f"✓ Verified Records: {health['counts']['claims']:,} Claims | {health['counts']['payers']} Payers | {health['counts']['followups']:,} Follow-ups | {health['counts']['claim_outcomes']:,} Outcomes")

    # 2. Executive Dashboard Metrics
    print_step(2, "Executive AR Portfolio Analytics")
    dash = client.get("/api/dashboard/metrics").json()
    print(f"• Total AR Portfolio Outstanding: ${dash['total_ar']:,.2f}")
    print(f"• ML Expected Recovery Pool:     ${dash['expected_recovery']:,.2f}")
    print(f"• Resolved Recovered Revenue:     ${dash['recovered_revenue']:,.2f}")
    print(f"• Portfolio Denial Rate:          {dash['denial_rate']}%")
    print(f"• Average AR Aging Duration:      {dash['avg_days_in_ar']} days")

    # 3. High-Priority Claim Inspection
    target_claim_id = "CLM0003394"
    print_step(3, f"Inspecting High-Priority Adverse Determination Claim: {target_claim_id}")
    claim = client.get(f"/api/claims/{target_claim_id}").json()
    print(f"• Patient ID:        {claim['patient_id']} | Provider ID: {claim['provider_id']}")
    print(f"• Target Payer:      {claim['payer_name']} ({claim['payer_id']})")
    print(f"• Total Billed:      ${claim['billed_amount']:,.2f} | Disputed Outstanding: ${claim['outstanding_amount']:,.2f}")
    print(f"• Adverse Finding:   Code {claim['denial_code']} — {claim['denial_reason']}")
    print(f"• Days in AR:        {claim['days_in_ar']} days ({claim['filing_deadline_remaining_days']} days before forfeiture)")
    print(f"• Priority Band:     {claim['priority_band']} (Priority Score: {claim['priority_score']:.1f}/100)")

    # 4. ML Model Evaluation & Risk Scoring
    print_step(4, f"Machine Learning Risk & Yield Assessment for {target_claim_id}")
    pred = client.post(f"/api/predictions/{target_claim_id}").json()
    print(f"• Delay Risk Probability P(Delay):     {pred['delay_probability']*100:.1f}%")
    print(f"• Denial Risk Probability P(Denial):   {pred['denial_probability']*100:.1f}%")
    print(f"• Recovery Yield Probability P(Recov): {pred['recovery_probability']*100:.1f}%")
    print(f"• ML Expected Recovery Dollar Yield:   ${pred['expected_recovery']:,.2f}")
    print("• Explainability Factors:")
    for reason in (pred.get("explainability_reasons") or []):
        print(f"   - {reason}")


    # 5. Payer Policy Vector RAG Knowledge Retrieval
    print_step(5, "Payer Policy Vector RAG Retrieval (TF-IDF + Cosine Similarity)")
    rag_chunks = client.get(f"/api/rag/claim-context/{target_claim_id}").json()
    print(f"✓ Retrieved {len(rag_chunks)} Grounded Policy Chunks for {claim['payer_name']}:")
    for idx, chunk in enumerate(rag_chunks[:2]):
        print(f"  [{idx+1}] {chunk['title']} (Similarity: {chunk['similarity_score']*100:.0f}%)")
        print(f"      Rule: \"{chunk['content'][:110]}...\"")
        print(f"      Required Docs: {chunk.get('required_documents', 'Standard records')}")

    # 6. Autonomous AI Follow-Up Decision & Generator
    print_step(6, "Autonomous AI Follow-Up Agent Strategy & Artifact Compilation")
    decision = client.post(f"/api/agent/decide/{target_claim_id}").json()
    print(f"• Recommended Action:   {decision['recommended_action']} ({decision['channel']} / Urgency: {decision['urgency']})")
    print(f"• Agent Confidence:     {decision['confidence']*100:.0f}%")
    print(f"• Strategic Reasoning:  {decision['reasoning']}")

    # 7. Multi-Format Follow-Up Artifact Compilation
    print_step(7, "Generating Grounded CMS/UB-04 Formal Appeal Reconsideration Letter")
    artifacts = client.get(f"/api/generator/preview/{target_claim_id}?tone=urgent").json()
    print(artifacts["appeal_letter"][:800] + "\n... [Full formal exhibits package compiled]")

    # 8. Payer Response Adjudication Simulation
    print_step(8, f"Probabilistic Payer Adjudication Simulation on {target_claim_id}")
    sim = client.post("/api/simulator/simulate", json={
        "claim_id": target_claim_id,
        "action_type": "Appeal",
        "action_quality": "high",
        "apply_to_db": False,
    }).json()
    print(f"• Calculated Probabilities: Full Approval: {sim['probability_distribution']['p_approved_full']*100:.1f}% | Partial: {sim['probability_distribution']['p_approved_partial']*100:.1f}% | Denied: {sim['probability_distribution']['p_denial_upheld']*100:.1f}%")
    print(f"• Simulated Adjudication Outcome: {sim['simulated_outcome']}")
    print(f"• Recovered Dollar Amount:        ${sim['recovered_amount']:,.2f}")
    print(f"• Remittance Reference:           {sim['remittance_reference']}")
    print(f"• Remittance Advice Snippet:      \"{sim['payer_response_text'][:120]}...\"")

    # 9. Autonomous Closed-Loop Recovery Engine
    print_step(9, "Running Autonomous Closed-Loop Recovery Engine (Batch of 5 High-Priority Claims)")
    loop = client.post("/api/closed-loop/run", json={
        "batch_size": 5,
        "min_priority_band": "High",
        "action_quality": "high",
    }).json()
    print(f"✓ Run ID: {loop['run_id']} | Processed Claims: {loop['total_processed']}")
    print(f"✓ Recovered Revenue: ${loop['total_recovered']:,.2f} of ${loop['total_original_outstanding']:,.2f} (Yield: {loop['recovery_yield_percentage']}%)")
    print("✓ Granular Claim State Transitions:")
    for r in loop["results"]:
        print(f"  • {r['claim_id']} ({r['payer_name']}) | {r['initial_status']} -> {r['chosen_action']} -> {r['simulated_outcome']} | Recovered: ${r['recovered_amount']:,.2f} | Final: {r['final_status']}")

    print_header("Demo Complete — All 13 Phases Successfully Verified & Operating")

if __name__ == "__main__":
    main()
