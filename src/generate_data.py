
import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

# -------------------------------
# 1. Project configuration
# -------------------------------
SEED = 20261022
OUTPUT_DIR = Path("data/raw")

fake = Faker()
fake.seed_instance(SEED)
random.seed(SEED)


def generate_data(employee_count=100, skill_count=20, project_count=15):
    """Generate reproducible workforce master data."""

    if employee_count < 1 or skill_count < 2 or project_count < 1:
        raise ValueError("Employees and projects must be positive; skills must be at least 2.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------
    # 2. Role master
    # -------------------------------
    role_names = [
        "Python Developer",
        "AI Engineer",
        "Data Engineer",
        "Data Analyst",
        "Software Tester",
        "Project Manager",
        "Cloud Engineer",
        "Frontend Developer",
        "Backend Developer",
        "Business Analyst",
    ]

    roles = pd.DataFrame([
        {
            "role_id": f"ROLE-{i + 1:06d}",
            "role_name": name,
            "active": True,
        }
        for i, name in enumerate(role_names)
    ])

    # -------------------------------
    # 3. Skill master
    # -------------------------------
    skill_names = [
        "Python", "SQL", "Machine Learning", "Deep Learning",
        "Data Analysis", "Pandas", "NumPy", "Power BI",
        "Tableau", "AWS", "Azure", "Docker", "Git",
        "JavaScript", "React", "HTML", "CSS", "Java",
        "Testing", "Communication", "Project Management",
        "Excel", "Statistics", "PyTorch", "TensorFlow",
        "NLP", "Computer Vision", "Spark", "Linux", "REST APIs",
    ]

    while len(skill_names) < skill_count:
        skill_names.append(
            f"Specialized Skill {len(skill_names) + 1}"
        )

    skill_names = skill_names[:skill_count]

    skills = pd.DataFrame([
        {
            "skill_id": f"SKL-{i + 1:06d}",
            "skill_name": name,
            "active": True,
            "validity_days": 365,
        }
        for i, name in enumerate(skill_names)
    ])

    # -------------------------------
    # 4. Employee master
    # -------------------------------
    employees = []
    today = date(2026, 10, 27)

    for i in range(employee_count):
        role = roles.iloc[i % len(roles)]
        is_part_time = random.random() < 0.15

        hire_date = fake.date_between(
            start_date=date(2021, 1, 1),
            end_date=date(2026, 1, 1),
        )

        employees.append({
            "employee_id": f"EMP-{i + 1:06d}",
            "employee_name": fake.name(),
            "role_id": role["role_id"],
            "employment_type": (
                "part_time" if is_part_time else "full_time"
            ),
            "weekly_hours": 20 if is_part_time else 40,
            "status": "active",
            "hire_date": hire_date.isoformat(),
        })

    employees = pd.DataFrame(employees)

    # -------------------------------
    # 5. EmployeeSkill bridge table
    # -------------------------------
    employee_skills = []

    for employee in employees.to_dict("records"):
        number_of_skills = random.randint(
            2, min(6, skill_count)
        )
        selected_skills = random.sample(
            skill_names, number_of_skills
        )

        for skill_name in selected_skills:
            skill_row = skills.loc[
                skills["skill_name"] == skill_name
            ].iloc[0]

            verified_date = today - timedelta(
                days=random.randint(0, 600)
            )

            employee_skills.append({
                "employee_skill_id": (
                    f"ES-{len(employee_skills) + 1:08d}"
                ),
                "employee_id": employee["employee_id"],
                "skill_id": skill_row["skill_id"],
                "proficiency": random.randint(1, 5),
                "last_verified_date": verified_date.isoformat(),
                "valid_until": (
                    verified_date + timedelta(days=365)
                ).isoformat(),
            })

    employee_skills = pd.DataFrame(employee_skills)

    # -------------------------------
    # 6. Project master
    # -------------------------------
    projects = []

    for i in range(project_count):
        manager = employees.iloc[i % employee_count]

        projects.append({
            "project_id": f"PRJ-2026-{i + 1:06d}",
            "project_name": f"{fake.catch_phrase()} Project",
            "project_manager_id": manager["employee_id"],
            "status": "active",
            "start_date": "2026-01-01",
            "end_date": "2027-12-31",
        })

    projects = pd.DataFrame(projects)

    # -------------------------------
    # 7. Export CSV files
    # -------------------------------
    tables = {
        "Employee": employees,
        "Role": roles,
        "Skill": skills,
        "EmployeeSkill": employee_skills,
        "Project": projects,
    }

    for name, table in tables.items():
        table.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)

    # -------------------------------
    # 8. Validate basic relationships
    # -------------------------------
    assert employees["employee_id"].is_unique
    assert roles["role_id"].is_unique
    assert skills["skill_id"].is_unique
    assert projects["project_id"].is_unique
    assert employee_skills["employee_skill_id"].is_unique

    assert employees["role_id"].isin(roles["role_id"]).all()
    assert employee_skills["employee_id"].isin(
        employees["employee_id"]
    ).all()
    assert employee_skills["skill_id"].isin(
        skills["skill_id"]
    ).all()
    assert projects["project_manager_id"].isin(
        employees["employee_id"]
    ).all()

    assert not employee_skills.duplicated(
        ["employee_id", "skill_id"]
    ).any()

    print("\nMaster data generated and validated!\n")

    for name, table in tables.items():
        print(f"{name}: {len(table):,} rows")

    print(f"\nCSV files saved in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate workforce master data."
    )

    parser.add_argument("--employees", type=int, default=100)
    parser.add_argument("--skills", type=int, default=20)
    parser.add_argument("--projects", type=int, default=15)
    parser.add_argument("--full", action="store_true")

    args = parser.parse_args()

    if args.full:
        args.employees = 5000
        args.skills = 300
        args.projects = 500

    if min(args.employees, args.skills, args.projects) < 1:
        parser.error("All dataset sizes must be positive.")

    if args.skills < 2:
        parser.error("At least 2 skills are required.")

    generate_data(
        employee_count=args.employees,
        skill_count=args.skills,
        project_count=args.projects,
    )
