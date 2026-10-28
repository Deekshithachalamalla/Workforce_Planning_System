
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

    with TemporaryDirectory(prefix="workforce_eligibility_check_") as temp:
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

            employees = bl.load_table("Employee")
            employee_skills = bl.load_table("EmployeeSkill")
            skills = bl.load_table("Skill")
            demand = bl.load_table("DemandPlan")

            profiles = employee_skills.merge(
                employees[["employee_id", "role_id", "status"]],
                on="employee_id",
                how="inner",
                validate="many_to_one",
            )

            profiles = profiles.merge(
                skills[["skill_id", "active"]],
                on="skill_id",
                how="inner",
                validate="many_to_one",
            )

            profiles["last_verified_date"] = pd.to_datetime(
                profiles["last_verified_date"], errors="coerce"
            )
            profiles["valid_until"] = pd.to_datetime(
                profiles["valid_until"], errors="coerce"
            )

            profiles["skill_is_current"] = (
                (
                    profiles["last_verified_date"]
                    >= bl.TODAY - pd.Timedelta(days=365)
                )
                & (profiles["valid_until"] >= bl.TODAY)
                & profiles["active"].eq(True)
            )

            if ledger.empty:
                print("Reservation ledger is empty.")
                print("PASS: No reservations violate eligibility.")
                return

            demand_fields = demand[
                [
                    "demand_id",
                    "role_id",
                    "skill_id",
                    "period",
                    "minimum_proficiency",
                ]
            ]

            # Attach the required role, skill and proficiency to each
            # reservation. Demand IDs must resolve to exactly one demand.
            checked = ledger.merge(
                demand_fields,
                on=["demand_id", "period"],
                how="left",
                validate="many_to_one",
                indicator=True,
            )

            checked = checked.merge(
                profiles[
                    [
                        "employee_id",
                        "role_id",
                        "skill_id",
                        "proficiency",
                        "status",
                        "skill_is_current",
                    ]
                ],
                on=["employee_id", "role_id", "skill_id"],
                how="left",
                validate="many_to_many",
            )

            checked["eligible"] = (
                checked["_merge"].eq("both")
                & checked["proficiency"].ge(
                    checked["minimum_proficiency"]
                )
                & checked["status"].eq("active")
                & checked["skill_is_current"].eq(True)
            )

            pair_results = checked.groupby(
                ["demand_id", "employee_id", "period"],
                dropna=False,
            ).agg(
                eligible=("eligible", "any"),
                reserved_hours=("reserved_hours", "sum"),
            )

            invalid = pair_results[~pair_results["eligible"]]

            print("\n=== Reservation Eligibility Verification ===")
            print(f"Demand gap records: {len(gaps):,}")
            print(f"Reservation ledger rows: {len(ledger):,}")
            print(f"Unique reservation pairs: {len(pair_results):,}")
            print(f"Ineligible reservation pairs: {len(invalid):,}")

            if not invalid.empty:
                print("\nFirst ineligible reservation pairs:")
                print(invalid.head(10).to_string())
                raise SystemExit(1)

            print(
                "\nPASS: Every reserved demand-employee pair has "
                "a matching profile satisfying the production "
                "eligibility rules."
            )

        finally:
            bl.RAW_DIR = original_raw_dir
            bl.PROCESSED_DIR = original_processed_dir


if __name__ == "__main__":
    main()
