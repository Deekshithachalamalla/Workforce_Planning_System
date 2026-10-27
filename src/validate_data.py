
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
TRUTH_PATH = Path("data/ground_truth/ground_truth.csv")
OUTPUT_DIR = Path("data/processed")

TODAY = pd.Timestamp("2026-10-27")
MAX_SKILL_AGE_DAYS = 365


def read_csv(name):
    path = RAW_DIR / f"{name}.csv"

    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    return pd.read_csv(path)


def detect_anomalies():
    allocations = read_csv("Allocation")
    availability = read_csv("Availability")
    demand = read_csv("DemandPlan")
    employee_skills = read_csv("EmployeeSkill")

    findings = []

    def report(issue_type, record_id, explanation):
        findings.append({
            "issue_type": issue_type,
            "record_id": record_id,
            "explanation": explanation,
        })

    # 1. Detect allocation exceeding availability.
    allocated = (
        allocations.groupby(
            ["employee_id", "period"],
            as_index=False,
        )["allocated_hours"]
        .sum()
    )

    capacity = availability[
        ["employee_id", "period", "available_hours"]
    ]

    reconciled = allocated.merge(
        capacity,
        on=["employee_id", "period"],
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    for _, row in reconciled.iterrows():
        if row["_merge"] != "both":
            report(
                "allocation_missing_availability",
                f"{row['employee_id']}:{row['period']}",
                "Allocation exists without a matching availability record.",
            )
        elif row["allocated_hours"] > row["available_hours"]:
            affected = allocations[
                (allocations["employee_id"] == row["employee_id"])
                & (allocations["period"] == row["period"])
            ]

            for allocation_id in affected["allocation_id"]:
                report(
                    "allocation_exceeds_availability",
                    allocation_id,
                    f"Total allocated hours {row['allocated_hours']} "
                    f"exceed available hours {row['available_hours']}.",
                )

    # 2. Detect stale skills claimed as current.
    if "claimed_current" in employee_skills.columns:
        employee_skills["last_verified_date"] = pd.to_datetime(
            employee_skills["last_verified_date"],
            errors="coerce",
        )

        employee_skills["valid_until"] = pd.to_datetime(
            employee_skills["valid_until"],
            errors="coerce",
        )

        stale = (
            employee_skills["claimed_current"].astype(str).str.lower().eq("true")
            & (
                employee_skills["last_verified_date"].isna()
                | (
                    employee_skills["last_verified_date"]
                    < TODAY - pd.Timedelta(days=MAX_SKILL_AGE_DAYS)
                )
                | employee_skills["valid_until"].isna()
                | (employee_skills["valid_until"] < TODAY)
            )
        )

        for _, row in employee_skills.loc[stale].iterrows():
            report(
                "stale_skill_treated_current",
                row["employee_skill_id"],
                "Skill is claimed current despite stale or expired verification.",
            )

    # 3. Detect duplicate demand using its business key.
    demand_key = [
        "project_id",
        "role_id",
        "skill_id",
        "period",
    ]

    duplicates = demand.duplicated(
        subset=demand_key,
        keep="first",
    )

    for _, row in demand.loc[duplicates].iterrows():
        report(
            "demand_double_counted",
            row["demand_id"],
            "Repeated project-role-skill-period demand.",
        )

    # 4. Detect assignments to multiple projects in one period.
    project_counts = allocations.groupby(
        ["employee_id", "period"]
    )["project_id"].nunique()

    overlapping_groups = project_counts[project_counts > 1]

    for (employee_id, period), _ in overlapping_groups.items():
        group = allocations[
            (allocations["employee_id"] == employee_id)
            & (allocations["period"] == period)
        ]

        # Report every allocation participating in the conflict.
        for _, row in group.iterrows():
            report(
                "employee_overlapping_projects",
                row["allocation_id"],
                f"Employee {employee_id} has allocations to multiple "
                f"projects during {period}.",
            )

    findings_df = pd.DataFrame(
        findings,
        columns=["issue_type", "record_id", "explanation"],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    findings_df.to_csv(
        OUTPUT_DIR / "anomaly_findings.csv",
        index=False,
    )

    # Compare detected anomaly labels with the separate ground truth.
    if not TRUTH_PATH.exists():
        raise FileNotFoundError(
            f"Missing ground-truth file: {TRUTH_PATH}"
        )

    truth = pd.read_csv(TRUTH_PATH)

    expected = truth[["issue_type", "record_id"]].drop_duplicates()
    detected = findings_df[["issue_type", "record_id"]].drop_duplicates()

    comparison = expected.merge(
        detected,
        on=["issue_type", "record_id"],
        how="left",
        indicator=True,
        validate="one_to_one",
    )

    comparison["detected"] = comparison["_merge"].eq("both")
    comparison = comparison.drop(columns="_merge")

    comparison.to_csv(
        OUTPUT_DIR / "ground_truth_evaluation.csv",
        index=False,
    )

    print("\nAnomaly detection completed!")
    print("Findings:", len(findings_df))
    print("Expected labelled anomalies:", len(expected))
    print(
        "Expected anomalies detected:",
        int(comparison["detected"].sum()),
        "of",
        len(comparison),
    )

    print("\nDetection counts by issue type:")
    if findings_df.empty:
        print("No anomalies detected.")
    else:
        print(findings_df["issue_type"].value_counts().to_string())

    print("\nOutput files:")
    print(OUTPUT_DIR / "anomaly_findings.csv")
    print(OUTPUT_DIR / "ground_truth_evaluation.csv")


if __name__ == "__main__":
    detect_anomalies()
