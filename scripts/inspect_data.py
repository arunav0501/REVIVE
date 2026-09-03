"""
AR Follow-Up AI - Dataset Inspection Script
Inspects CSV files in data/ directory and reports column schemas, row counts, and summary stats.
"""

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

EXPECTED_FILES = [
    "claims.csv",
    "followups.csv",
    "claim_outcomes.csv",
    "ml_predictions_training.csv",
    "payers.csv",
    "payer_policies.csv",
]


def inspect_dataset():
    print("=" * 60)
    print("AR FOLLOW-UP AI - DATASET INSPECTION")
    print("=" * 60)

    for filename in EXPECTED_FILES:
        filepath = DATA_DIR / filename
        if not filepath.exists():
            print(f"[-] MISSING: {filename}")
            continue

        df = pd.read_csv(filepath)
        print(f"\n[+] {filename}")
        print(f"    Rows: {len(df):,}, Columns: {len(df.columns)}")
        print(f"    Columns: {list(df.columns)}")
        print(f"    Null Counts:\n{df.isnull().sum()[df.isnull().sum() > 0]}")


if __name__ == "__main__":
    inspect_dataset()
