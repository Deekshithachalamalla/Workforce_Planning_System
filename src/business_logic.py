
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

TODAY = pd.Timestamp("2026-10-27")
MIN_PROFICIENCY = 3


def load_table(name):
    """Read a generated CSV file."""
    path = RAW_DIR / f"{name}.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run the data generators first."
        )

    return pd.read_csv(path)


def calculate_utilization():
    """Calculate employee capacity and utilization per week."""

    employees = load_table("Employee")
    availability = load_table("Availability")
    allocations = load_table("Allocation")

    allocated = (
        allocations.groupby(
            ["employee_id", "period"],
            as_index=False,
        )["allocated_hours"]
        .sum()
        .rename(columns={
            "allocated_hours": "total_allocated_hours"
        })
    )

    result = availability.merge(
        employees[[
            "employee_id",
            "role_id",
            "employment_type",
        ]],
        on="employee_id",
        how="left",
        validate="many_to_one",
    )

    result = result.merge(
        allocated,
        on=["employee_id", "period"],
        how="left",
        validate="one_to_one",
    )

    result["total_allocated_hours"] = (
        result["total_allocated_hours"].fillna(0)
    )

    result["capacity_balance_hours"] = (
        result["available_hours"]
        - result["total_allocated_hours"]
    )

    result["utilization_pct"] = (
        result["total_allocated_hours"]
        .div(result["available_hours"].where(
            result["available_hours"] > 0
        ))
        .mul(100)
        .round(2)
    )

    result["utilization_status"] = "normal"

    result.loc[
        result["available_hours"] == 0,
        "utilization_status",
    ] = "no_available_capacity"

    result.loc[
        result["utilization_pct"] > 100,
        "utilization_status",
    ] = "overallocated"

    result.loc[
        result["utilization_pct"] >= 85,
        "utilization_status",
    ] = "high_utilization"

    # An overallocation must take precedence over high utilization.
    result.loc[
        result["total_allocated_hours"] > result["available_hours"],
        "utilization_status",
    ] = "overallocated"

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    result.to_csv(
        PROCESSED_DIR / "utilization.csv",
        index=False,
    )

    return result


def calculate_skill_gaps():
    """Compare project demand with allocations and qualified capacity."""

    employees = load_table("Employee")
    skills = load_table("Skill")
    employee_skills = load_table("EmployeeSkill")
    demand = load_table("DemandPlan")
    allocations = load_table("Allocation")
    availability = load_table("Availability")

    # Aggregate allocations against each individual demand record.
    allocated_by_demand = (
        allocations.groupby("demand_id", as_index=False)
        ["allocated_hours"]
        .sum()
        .rename(columns={
            "allocated_hours": "assigned_hours"
        })
    )

    demand = demand.merge(
        allocated_by_demand,
        on="demand_id",
        how="left",
        validate="one_to_one",
    )

    demand["assigned_hours"] = (
        demand["assigned_hours"].fillna(0)
    )

    demand["uncovered_hours"] = (
        demand["required_hours"] - demand["assigned_hours"]
    ).clip(lower=0)

    # Join skill profiles with employees and skills.
    profiles = employee_skills.merge(
        employees[["employee_id", "role_id", "status"]],
        on="employee_id",
        how="inner",
        validate="many_to_one",
    )

    profiles = profiles.merge(
        skills[["skill_id", "skill_name", "active"]],
        on="skill_id",
        how="inner",
        validate="many_to_one",
    )

    profiles["last_verified_date"] = pd.to_datetime(
        profiles["last_verified_date"],
        errors="coerce",
    )

    profiles["valid_until"] = pd.to_datetime(
        profiles["valid_until"],
        errors="coerce",
    )

    profiles["skill_is_current"] = (
        (profiles["last_verified_date"] >= TODAY - pd.Timedelta(days=365))
        & (profiles["valid_until"] >= TODAY)
        & profiles["active"].eq(True)
    )

    # Count qualified, current-skill capacity for each demand line.
    availability_lookup = availability.set_index(
        ["employee_id", "period"]
    )["available_hours"].to_dict()

    allocation_lookup = (
        allocations.groupby(
            ["employee_id", "period"]
        )["allocated_hours"]
        .sum()
        .to_dict()
    )

    gap_rows = []

    for row in demand.to_dict("records"):
        eligible = profiles[
            (profiles["role_id"] == row["role_id"])
            & (profiles["skill_id"] == row["skill_id"])
            & (profiles["proficiency"] >= row["minimum_proficiency"])
            & (profiles["status"] == "active")
            & (profiles["skill_is_current"])
        ]

        qualified_remaining_hours = 0.0

        for employee_id in eligible["employee_id"].unique():
            available_hours = availability_lookup.get(
                (employee_id, row["period"]), 0
            )

            allocated_hours = allocation_lookup.get(
                (employee_id, row["period"]), 0
            )

            qualified_remaining_hours += max(
                0,
                available_hours - allocated_hours,
            )

        gap_hours = max(
            0,
            row["required_hours"] - row["assigned_hours"],
        )

        if gap_hours == 0:
            action = "no_action"
        elif qualified_remaining_hours >= gap_hours:
            action = "reallocate_or_assign"
        elif qualified_remaining_hours > 0:
            action = "reallocate_and_train_or_hire"
        else:
            action = "train_or_hire"

        gap_rows.append({
            "gap_id": f"GAP-{row['demand_id']}",
            "demand_id": row["demand_id"],
            "project_id": row["project_id"],
            "role_id": row["role_id"],
            "skill_id": row["skill_id"],
            "period": row["period"],
            "required_hours": row["required_hours"],
            "assigned_hours": row["assigned_hours"],
            "uncovered_hours": gap_hours,
            "qualified_remaining_hours": qualified_remaining_hours,
            "recommended_action": action,
        })

    gaps = pd.DataFrame(gap_rows)

    gaps = gaps.merge(
        skills[["skill_id", "skill_name"]],
        on="skill_id",
        how="left",
        validate="many_to_one",
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    gaps.to_csv(
        PROCESSED_DIR / "GapAnalysis.csv",
        index=False,
    )

    return gaps


def main():
    utilization = calculate_utilization()
    gaps = calculate_skill_gaps()

    print("\nBusiness calculations completed!\n")

    print("Employee-period records:", len(utilization))
    print("Demand-gap records:", len(gaps))

    print(
        "Overallocated employee-periods:",
        int((utilization["utilization_status"] == "overallocated").sum()),
    )

    print(
        "Demand lines with uncovered hours:",
        int((gaps["uncovered_hours"] > 0).sum()),
    )

    print(
        "Total uncovered demand hours:",
        round(float(gaps["uncovered_hours"].sum()), 2),
    )

    print("\nOutput files:")
    print(PROCESSED_DIR / "utilization.csv")
    print(PROCESSED_DIR / "GapAnalysis.csv")


if __name__ == "__main__":
    main()
