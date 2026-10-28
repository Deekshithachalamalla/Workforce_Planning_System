
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import business_logic as bl


def main():
    original_raw_dir = bl.RAW_DIR
    original_processed_dir = bl.PROCESSED_DIR

    with TemporaryDirectory(prefix="workforce_capacity_check_") as temp:
        temp_dir = Path(temp)
        raw_copy = temp_dir / "raw"
        processed_copy = temp_dir / "processed"

        shutil.copytree(original_raw_dir, raw_copy)
        processed_copy.mkdir()

        bl.RAW_DIR = raw_copy
        bl.PROCESSED_DIR = processed_copy

        try:
            gaps, ledger = bl.calculate_skill_gaps(
                return_reservations=True
            )

            availability = pd.read_csv(
                raw_copy / "Availability.csv"
            )
            allocations = pd.read_csv(
                raw_copy / "Allocation.csv"
            )

            capacity = availability.groupby(
                ["employee_id", "period"]
            )["available_hours"].sum()

            committed = allocations.groupby(
                ["employee_id", "period"]
            )["allocated_hours"].sum()

            remaining = (
                capacity.sub(committed, fill_value=0)
                .clip(lower=0)
                .rename("remaining_capacity")
                .reset_index()
            )

            if ledger.empty:
                totals = pd.DataFrame(
                    columns=[
                        "employee_id",
                        "period",
                        "reserved_hours",
                    ]
                )
            else:
                totals = ledger.groupby(
                    ["employee_id", "period"],
                    as_index=False,
                )["reserved_hours"].sum()

            check = remaining.merge(
                totals,
                on=["employee_id", "period"],
                how="left",
            )
            check["reserved_hours"] = (
                check["reserved_hours"].fillna(0)
            )
            check["excess_hours"] = (
                check["reserved_hours"]
                - check["remaining_capacity"]
            )

            violations = check[
                check["excess_hours"] > 1e-9
            ]

            print("\n=== Production Reservation Verification ===")
            print(f"Gap rows: {len(gaps):,}")
            print(f"Reservation ledger rows: {len(ledger):,}")
            print(f"Employee-period capacity records: {len(check):,}")
            print(
                "Total proposed reserved hours: "
                f"{ledger['reserved_hours'].sum():,.2f}"
                if not ledger.empty
                else "Total proposed reserved hours: 0.00"
            )
            print(f"Capacity violations: {len(violations):,}")

            if not violations.empty:
                print("\nFirst capacity violations:")
                print(violations.head(10).to_string(index=False))
                raise SystemExit(1)

            print(
                "\nPASS: Proposed reservations do not exceed "
                "remaining employee capacity."
            )

        finally:
            bl.RAW_DIR = original_raw_dir
            bl.PROCESSED_DIR = original_processed_dir


if __name__ == "__main__":
    main()
