
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
TRUTH_DIR = Path("data/ground_truth")


def inject_anomalies():
    # Load existing generated records.
    employees = pd.read_csv(RAW_DIR / "Employee.csv")
    skills = pd.read_csv(RAW_DIR / "Skill.csv")
    employee_skills = pd.read_csv(
        RAW_DIR / "EmployeeSkill.csv"
    )
    projects = pd.read_csv(RAW_DIR / "Project.csv")
    demand = pd.read_csv(RAW_DIR / "DemandPlan.csv")
    availability = pd.read_csv(RAW_DIR / "Availability.csv")
    allocations = pd.read_csv(RAW_DIR / "Allocation.csv")

    truth = []

    def label(issue_type, entity_type, record_id, explanation):
        truth.append({
            "issue_id": f"ISSUE-{len(truth) + 1:04d}",
            "issue_type": issue_type,
            "entity_type": entity_type,
            "record_id": record_id,
            "expected_decision": explanation,
        })

    # ------------------------------------------
    # 1. Allocation exceeds employee availability
    # ------------------------------------------
    allocation = allocations.iloc[0]
    employee_id = allocation["employee_id"]
    period = allocation["period"]

    availability_match = (
        (availability["employee_id"] == employee_id)
        & (availability["period"] == period)
    )

    available_hours = float(
        availability.loc[
            availability_match, "available_hours"
        ].iloc[0]
    )

    employee_allocations = (
        (allocations["employee_id"] == employee_id)
        & (allocations["period"] == period)
    )

    current_total = allocations.loc[
        employee_allocations, "allocated_hours"
    ].sum()

    # Increase one allocation enough to exceed capacity.
    allocations.loc[
        allocations["allocation_id"] == allocation["allocation_id"],
        "allocated_hours",
    ] += available_hours + 1

    label(
        "allocation_exceeds_availability",
        "Allocation",
        allocation["allocation_id"],
        f"Flag when total allocated hours exceed {available_hours} available hours.",
    )

    # ------------------------------------------
    # 2. Stale skill incorrectly claimed current
    # ------------------------------------------
    skill_index = employee_skills.index[0]
    skill_record_id = employee_skills.loc[
        skill_index, "employee_skill_id"
    ]

    employee_skills["claimed_current"] = False

    # Deliberately make this skill verification stale.
    employee_skills.loc[
        skill_index, "last_verified_date"
    ] = "2024-01-01"

    # Contradictory claim used as a negative test case.
    employee_skills.loc[
        skill_index, "claimed_current"
    ] = True

    label(
        "stale_skill_treated_current",
        "EmployeeSkill",
        skill_record_id,
        "Flag a skill claimed current despite stale verification.",
    )

    # ------------------------------------------
    # 3. Duplicate project demand
    # ------------------------------------------
    original = demand.iloc[0].copy()
    duplicate = original.copy()

    duplicate["demand_id"] = (
        "DEM-DUP-" + str(len(demand) + 1).zfill(6)
    )

    duplicate_id = duplicate["demand_id"]
    demand = pd.concat(
        [demand, pd.DataFrame([duplicate])],
        ignore_index=True,
    )

    label(
        "demand_double_counted",
        "DemandPlan",
        duplicate_id,
        "Flag duplicate project-role-skill-period demand.",
    )

    # ------------------------------------------
    # 4. Employee assigned to overlapping projects
    # ------------------------------------------
    first_allocation = allocations.iloc[0]
    employee_id = first_allocation["employee_id"]
    period = first_allocation["period"]
    first_project = first_allocation["project_id"]

    other_projects = projects.loc[
        projects["project_id"] != first_project,
        "project_id",
    ]

    second_project = other_projects.iloc[0]

    matching_demand = demand.loc[
        (demand["project_id"] == second_project)
        & (demand["period"] == period)
    ]

    if matching_demand.empty:
        matching_demand = demand.loc[
            demand["project_id"] == second_project
        ]

    if matching_demand.empty:
        raise RuntimeError(
            "Could not find a demand record for the second project."
        )

    target_demand = matching_demand.iloc[0]

    overlapping_id = (
        f"ALLOC-ANOM-{len(allocations) + 1:06d}"
    )

    overlapping = {
        "allocation_id": overlapping_id,
        "employee_id": employee_id,
        "project_id": second_project,
        "demand_id": target_demand["demand_id"],
        "period": period,
        "allocated_hours": 8,
    }

    allocations = pd.concat(
        [allocations, pd.DataFrame([overlapping])],
        ignore_index=True,
    )

    label(
        "employee_overlapping_projects",
        "Allocation",
        overlapping_id,
        "Flag the employee assigned to multiple projects in the same period.",
    )

    # ------------------------------------------
    # Save altered records and separate truth
    # ------------------------------------------
    allocations.to_csv(
        RAW_DIR / "Allocation.csv", index=False
    )
    employee_skills.to_csv(
        RAW_DIR / "EmployeeSkill.csv", index=False
    )
    demand.to_csv(
        RAW_DIR / "DemandPlan.csv", index=False
    )

    TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(truth).to_csv(
        TRUTH_DIR / "ground_truth.csv",
        index=False,
    )

    print("\nFour anomaly scenarios injected!")
    print("Ground-truth labels:", len(truth))
    print("Ground-truth file:", TRUTH_DIR / "ground_truth.csv")
    print("Input records updated in:", RAW_DIR.resolve())


if __name__ == "__main__":
    inject_anomalies()
