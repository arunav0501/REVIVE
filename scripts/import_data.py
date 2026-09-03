"""
AR Follow-Up AI - Data Import & Seeding Script (Phase 2)

Loads synthetic claims, payers, policies, follow-ups, and outcome datasets
from CSV files, validates schemas and relationships, cleans types, and imports
them into the SQLite database.
"""

import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database.session import Base, engine, SessionLocal
from backend.app.models import (
    Claim,
    Payer,
    PayerPolicy,
    Followup,
    ClaimOutcome,
)

DATA_DIR = PROJECT_ROOT / "data"


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN / Inf / float('nan') with None for clean SQL NULL insertion."""
    return df.replace({np.nan: None})


def import_payers(session) -> int:
    path = DATA_DIR / "payers.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)
    df = clean_dataframe(df)

    # Validate duplicates
    if df["payer_id"].duplicated().any():
        raise ValueError("Duplicate payer_id detected in payers.csv")

    records = [
        Payer(
            payer_id=str(row["payer_id"]).strip(),
            payer_name=str(row["payer_name"]).strip(),
            plan_type=str(row["plan_type"]).strip(),
            avg_processing_days=int(row["avg_processing_days"]),
            avg_response_days=int(row["avg_response_days"]),
            filing_deadline_days=int(row["filing_deadline_days"]),
            preferred_contact_method=str(row["preferred_contact_method"]).strip(),
        )
        for _, row in df.iterrows()
    ]
    session.bulk_save_objects(records)
    session.commit()
    return len(records)


def import_payer_policies(session) -> int:
    path = DATA_DIR / "payer_policies.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)
    df = clean_dataframe(df)

    if df["payer_id"].duplicated().any():
        raise ValueError("Duplicate payer_id detected in payer_policies.csv")

    records = [
        PayerPolicy(
            payer_id=str(row["payer_id"]).strip(),
            payer_name=str(row["payer_name"]).strip(),
            policy_document=str(row["policy_document"]).strip(),
            filing_deadline_days=int(row["filing_deadline_days"]),
            preferred_contact_method=str(row["preferred_contact_method"]).strip(),
            average_processing_days=int(row["average_processing_days"]),
            average_response_days=int(row["average_response_days"]),
            required_documents=str(row["required_documents"]).strip() if row["required_documents"] else None,
            escalation_after_days=int(row["escalation_after_days"]),
            policy_text=str(row["policy_text"]).strip(),
        )
        for _, row in df.iterrows()
    ]
    session.bulk_save_objects(records)
    session.commit()
    return len(records)


def import_claims(session, batch_size=2000) -> int:
    path = DATA_DIR / "claims.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)
    df = clean_dataframe(df)

    if df["claim_id"].duplicated().any():
        raise ValueError("Duplicate claim_id detected in claims.csv")

    records = []
    total = len(df)
    for idx, row in df.iterrows():
        # Clean boolean / nullable types
        auth_req = bool(row["authorization_required"]) if row["authorization_required"] is not None else False
        days_since_resp = int(row["days_since_last_response"]) if row["days_since_last_response"] is not None else None

        claim = Claim(
            claim_id=str(row["claim_id"]).strip(),
            patient_id=str(row["patient_id"]).strip(),
            provider_id=str(row["provider_id"]).strip(),
            payer_id=str(row["payer_id"]).strip(),
            claim_date=str(row["claim_date"]).strip(),
            service_date=str(row["service_date"]).strip(),
            claim_type=str(row["claim_type"]).strip(),
            place_of_service=str(row["place_of_service"]).strip(),
            billed_amount=float(row["billed_amount"]),
            allowed_amount=float(row["allowed_amount"]),
            paid_amount=float(row["paid_amount"]),
            patient_responsibility=float(row["patient_responsibility"]),
            outstanding_amount=float(row["outstanding_amount"]),
            expected_reimbursement=float(row["expected_reimbursement"]),
            claim_status=str(row["claim_status"]).strip(),
            denial_status=str(row["denial_status"]).strip() if row["denial_status"] else None,
            denial_code=str(row["denial_code"]).strip() if row["denial_code"] else None,
            denial_reason=str(row["denial_reason"]).strip() if row["denial_reason"] else None,
            days_in_ar=int(row["days_in_ar"]),
            followup_count=int(row["followup_count"]),
            resubmission_count=int(row["resubmission_count"]),
            appeal_status=str(row["appeal_status"]).strip() if row["appeal_status"] else "Not Applicable",
            authorization_required=auth_req,
            authorization_status=str(row["authorization_status"]).strip() if row["authorization_status"] else "Not Required",
            network_status=str(row["network_status"]).strip() if row["network_status"] else "In-Network",
            last_followup_date=str(row["last_followup_date"]).strip() if row["last_followup_date"] else None,
            last_payer_response=str(row["last_payer_response"]).strip() if row["last_payer_response"] else None,
            days_since_last_response=days_since_resp,
        )
        records.append(claim)

        if len(records) >= batch_size:
            session.bulk_save_objects(records)
            session.commit()
            records = []

    if records:
        session.bulk_save_objects(records)
        session.commit()

    return total


def import_followups(session, batch_size=2000) -> int:
    path = DATA_DIR / "followups.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)
    df = clean_dataframe(df)

    if df["followup_id"].duplicated().any():
        raise ValueError("Duplicate followup_id detected in followups.csv")

    records = []
    total = len(df)
    for idx, row in df.iterrows():
        resp_date = str(row["response_date"]).strip() if row["response_date"] else None
        payer_resp = str(row["payer_response"]).strip() if row["payer_response"] else None
        outcome = str(row["outcome"]).strip() if row["outcome"] else None

        fu = Followup(
            followup_id=str(row["followup_id"]).strip(),
            claim_id=str(row["claim_id"]).strip(),
            followup_date=str(row["followup_date"]).strip(),
            channel=str(row["channel"]).strip(),
            action_type=str(row["action_type"]).strip(),
            message=str(row["message"]).strip(),
            payer_response=payer_resp,
            response_date=resp_date,
            outcome=outcome,
        )
        records.append(fu)

        if len(records) >= batch_size:
            session.bulk_save_objects(records)
            session.commit()
            records = []

    if records:
        session.bulk_save_objects(records)
        session.commit()

    return total


def import_claim_outcomes(session, batch_size=2000) -> int:
    path = DATA_DIR / "claim_outcomes.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)
    df = clean_dataframe(df)

    if df["claim_id"].duplicated().any():
        raise ValueError("Duplicate claim_id detected in claim_outcomes.csv")

    records = []
    total = len(df)
    for idx, row in df.iterrows():
        outcome = ClaimOutcome(
            claim_id=str(row["claim_id"]).strip(),
            final_outcome=str(row["final_outcome"]).strip(),
            days_to_resolution=int(row["days_to_resolution"]),
            was_denied=int(row["was_denied"]),
            was_delayed=int(row["was_delayed"]),
            recovered_amount=float(row["recovered_amount"]),
            successful_followup=int(row["successful_followup"]),
        )
        records.append(outcome)

        if len(records) >= batch_size:
            session.bulk_save_objects(records)
            session.commit()
            records = []

    if records:
        session.bulk_save_objects(records)
        session.commit()

    return total


def run_data_import():
    start_time = time.time()
    print("==================================================")
    print("RECOVERAI / AR FOLLOW-UP AI - DATABASE IMPORT")
    print("==================================================")
    print("1. Creating SQLite database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("   ✓ Schema created successfully.")

    session = SessionLocal()
    try:
        print("\n2. Importing Payers...")
        n_payers = import_payers(session)
        print(f"   ✓ Imported {n_payers} Payers.")

        print("\n3. Importing Payer Policies...")
        n_policies = import_payer_policies(session)
        print(f"   ✓ Imported {n_policies} Payer Policies.")

        print("\n4. Importing Claims...")
        n_claims = import_claims(session)
        print(f"   ✓ Imported {n_claims:,} Claims.")

        print("\n5. Importing Follow-Ups...")
        n_followups = import_followups(session)
        print(f"   ✓ Imported {n_followups:,} Follow-Ups.")

        print("\n6. Importing Claim Outcomes...")
        n_outcomes = import_claim_outcomes(session)
        print(f"   ✓ Imported {n_outcomes:,} Claim Outcomes.")

        elapsed = time.time() - start_time
        print("\n==================================================")
        print("IMPORT VERIFICATION SUMMARY:")
        print(f"  • Payers:         {session.query(Payer).count():>6,}")
        print(f"  • Payer Policies: {session.query(PayerPolicy).count():>6,}")
        print(f"  • Claims:         {session.query(Claim).count():>6,}")
        print(f"  • Follow-Ups:     {session.query(Followup).count():>6,}")
        print(f"  • Claim Outcomes: {session.query(ClaimOutcome).count():>6,}")
        print(f"  • Total Duration: {elapsed:.2f} seconds")
        print("==================================================")
        print("✓ Database import completed successfully!")
    except Exception as e:
        session.rollback()
        print(f"\n[!] ERROR during import: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_data_import()
