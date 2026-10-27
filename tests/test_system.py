
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
TRUTH = ROOT / "data" / "ground_truth" / "ground_truth.csv"


def read_raw(name):
    return pd.read_csv(RAW / f"{name}.csv")


def test_master_table_ids_are_unique():
    employees = read_raw("Employee")
    roles = read_raw("Role")
    skills = read_raw("Skill")
    projects = read_raw("Project")

    assert employees["employee_id"].is_unique
    assert roles["role_id"].is_unique
    assert skills["skill_id"].is_unique
    assert projects["project_id"].is_unique


def test_master_foreign_keys_are_valid():
    employees = read_raw("Employee")
    roles = read_raw("Role")
    skills = read_raw("Skill")
    employee_skills = read_raw("EmployeeSkill")
    projects = read_raw("Project")

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


def test_transaction_foreign_keys_are_valid():
    employees = read_raw("Employee")
    projects = read_raw("Project")
    demand = read_raw("DemandPlan")
    allocations = read_raw("Allocation")
    availability = read_raw("Availability")
    training = read_raw("Training")

    assert demand["project_id"].isin(projects["project_id"]).all()
    assert allocations["employee_id"].isin(
        employees["employee_id"]
    ).all()
    assert allocations["project_id"].isin(
        projects["project_id"]
    ).all()
    assert allocations["demand_id"].isin(
        demand["demand_id"]
    ).all()
    assert availability["employee_id"].isin(
        employees["employee_id"]
    ).all()
    assert training["employee_id"].isin(
        employees["employee_id"]
    ).all()


def test_capacity_and_utilization_outputs_exist():
    utilization_path = PROCESSED / "utilization.csv"
    gaps_path = PROCESSED / "GapAnalysis.csv"

    assert utilization_path.exists()
    assert gaps_path.exists()

    utilization = pd.read_csv(utilization_path)

    required_columns = {
        "employee_id",
        "period",
        "available_hours",
        "total_allocated_hours",
        "capacity_balance_hours",
        "utilization_status",
    }

    assert required_columns.issubset(utilization.columns)

    expected_balance = (
        utilization["available_hours"]
        - utilization["total_allocated_hours"]
    )

    assert (
        expected_balance
        == utilization["capacity_balance_hours"]
    ).all()


def test_all_four_labelled_anomalies_were_detected():
    evaluation_path = PROCESSED / "ground_truth_evaluation.csv"

    assert TRUTH.exists()
    assert evaluation_path.exists()

    truth = pd.read_csv(TRUTH)
    evaluation = pd.read_csv(evaluation_path)

    assert len(truth) == 4
    assert evaluation["detected"].astype(bool).all()


def test_ground_truth_is_separate_from_demand_inputs():
    demand = read_raw("DemandPlan")

    # Ground-truth labels must not be copied into the demand input.
    assert "issue_type" not in demand.columns
    assert "expected_decision" not in demand.columns
