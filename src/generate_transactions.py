
import random
from pathlib import Path

import pandas as pd

SEED = 20261022
RAW_DIR = Path("data/raw")
GROUND_TRUTH_DIR = Path("data/ground_truth")


def generate_transactions():
    # Reset the random generator for reproducible data.
    random.seed(SEED)

    # Check that master data exists.
    required_files = [
        "Employee.csv",
        "Role.csv",
        "Skill.csv",
        "EmployeeSkill.csv",
        "Project.csv",
    ]

    for filename in required_files:
        if not (RAW_DIR / filename).exists():
            raise FileNotFoundError(
                f"Missing {RAW_DIR / filename}. "
                "Run generate_data.py first."
            )

    employees = pd.read_csv(RAW_DIR / "Employee.csv")
    roles = pd.read_csv(RAW_DIR / "Role.csv")
    skills = pd.read_csv(RAW_DIR / "Skill.csv")
    projects = pd.read_csv(RAW_DIR / "Project.csv")

    # Index employees by role.
    employees_by_role = {
        role_id: group["employee_id"].tolist()
        for role_id, group in employees.groupby("role_id")
    }

    skill_ids = skills["skill_id"].tolist()
    role_ids = roles["role_id"].tolist()

    demand_rows = []
    availability_rows = []
    allocation_rows = []
    training_rows = []

    employee_records = employees.to_dict("records")
    project_records = projects.to_dict("records")

    # Generate 52 weekly periods for 2026.
    for week in range(1, 53):
        period = f"2026W{week:02d}"

        weekly_capacity = {}

        # Create availability for every employee.
        for employee in employee_records:
            employee_id = employee["employee_id"]
            normal_hours = float(employee["weekly_hours"])

            leave_hours = (
                random.choice([4, 8, 16])
                if random.random() < 0.08
                else 0
            )

            available_hours = max(0, normal_hours - leave_hours)
            weekly_capacity[employee_id] = available_hours

            availability_rows.append({
                "availability_id": f"AV-{employee_id}-{period}",
                "employee_id": employee_id,
                "period": period,
                "weekly_capacity_hours": normal_hours,
                "leave_hours": leave_hours,
                "available_hours": available_hours,
            })

        # Baseline rule: an employee can be allocated to at most
        # one project in a given week.
        assigned_employees_this_week = set()

        # Create project demand.
        for project in project_records:
            number_of_demand_lines = random.randint(1, 3)
            used_demand_pairs = set()

            for line in range(1, number_of_demand_lines + 1):

                # Ensure each project/week has unique role-skill pairs.
                available_pairs = [
                    (role_id, skill_id)
                    for role_id in role_ids
                    for skill_id in skill_ids
                    if (role_id, skill_id) not in used_demand_pairs
                ]

                if not available_pairs:
                    break

                role_id, skill_id = random.choice(available_pairs)
                used_demand_pairs.add((role_id, skill_id))

                required_hours = random.choice([20, 40, 60, 80])
                minimum_proficiency = random.randint(2, 4)

                demand_id = (
                    f"DEM-{project['project_id']}-{period}"
                    f"-R{line:02d}"
                )

                demand_rows.append({
                    "demand_id": demand_id,
                    "project_id": project["project_id"],
                    "role_id": role_id,
                    "skill_id": skill_id,
                    "period": period,
                    "required_hours": required_hours,
                    "minimum_proficiency": minimum_proficiency,
                    "status": "planned",
                })

                # Select an employee with the requested role who
                # has not already been assigned to another project.
                candidates = [
                    employee_id
                    for employee_id in employees_by_role.get(role_id, [])
                    if employee_id not in assigned_employees_this_week
                    and weekly_capacity.get(employee_id, 0) > 0
                ]

                if candidates:
                    employee_id = random.choice(candidates)

                    allocated_hours = min(
                        required_hours,
                        weekly_capacity[employee_id],
                    )

                    if allocated_hours > 0:
                        allocation_rows.append({
                            "allocation_id": (
                                f"ALLOC-{period}-"
                                f"{len(allocation_rows) + 1:07d}"
                            ),
                            "employee_id": employee_id,
                            "project_id": project["project_id"],
                            "demand_id": demand_id,
                            "period": period,
                            "allocated_hours": allocated_hours,
                        })

                        weekly_capacity[employee_id] -= allocated_hours
                        assigned_employees_this_week.add(employee_id)

        # Generate optional training records.
        if employee_records and random.random() < 0.30:
            employee = random.choice(employee_records)
            skill_id = random.choice(skill_ids)

            training_rows.append({
                "training_id": f"TRN-2026-{week:04d}",
                "employee_id": employee["employee_id"],
                "skill_id": skill_id,
                "period": period,
                "planned_hours": 8,
                "status": "planned",
            })

    # Build transaction tables.
    tables = {
        "DemandPlan": pd.DataFrame(demand_rows),
        "Availability": pd.DataFrame(availability_rows),
        "Allocation": pd.DataFrame(allocation_rows),
        "Training": pd.DataFrame(training_rows),
    }

    # Validate unique identifiers.
    for name, table in tables.items():
        if not table.empty:
            id_column = {
                "DemandPlan": "demand_id",
                "Availability": "availability_id",
                "Allocation": "allocation_id",
                "Training": "training_id",
            }[name]

            assert table[id_column].is_unique, (
                f"Duplicate IDs found in {name}"
            )

    # Validate foreign keys.
    assert tables["DemandPlan"]["project_id"].isin(
        projects["project_id"]
    ).all()

    assert tables["DemandPlan"]["role_id"].isin(
        roles["role_id"]
    ).all()

    assert tables["DemandPlan"]["skill_id"].isin(
        skills["skill_id"]
    ).all()

    assert tables["Availability"]["employee_id"].isin(
        employees["employee_id"]
    ).all()

    assert tables["Allocation"]["employee_id"].isin(
        employees["employee_id"]
    ).all()

    assert tables["Allocation"]["project_id"].isin(
        projects["project_id"]
    ).all()

    assert tables["Allocation"]["demand_id"].isin(
        tables["DemandPlan"]["demand_id"]
    ).all()

    assert tables["Training"]["employee_id"].isin(
        employees["employee_id"]
    ).all()

    assert tables["Training"]["skill_id"].isin(
        skills["skill_id"]
    ).all()

    # Check baseline allocations do not exceed availability.
    if not tables["Allocation"].empty:
        allocated = tables["Allocation"].groupby(
            ["employee_id", "period"]
        )["allocated_hours"].sum()

        available = tables["Availability"].set_index(
            ["employee_id", "period"]
        )["available_hours"]

        assert (allocated <= available.loc[allocated.index]).all(), (
            "Baseline allocations exceed employee availability."
        )

    # Save transaction data.
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for name, table in tables.items():
        table.to_csv(RAW_DIR / f"{name}.csv", index=False)

    # Do not erase ground truth here. It is created by the anomaly
    # injection step after the baseline transaction data is generated.

    print("\nTransaction data generated successfully!")

    for name, table in tables.items():
        print(f"{name}: {len(table):,} rows")

    print("\nBasic ID, foreign-key, and capacity checks passed.")
    print("Files saved in:", RAW_DIR.resolve())


if __name__ == "__main__":
    generate_transactions()
