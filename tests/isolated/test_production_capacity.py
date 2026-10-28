import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import business_logic as bl


def test_production_capacity_reservations_use_shared_capacity(
    tmp_path, monkeypatch
):
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw.mkdir()
    processed.mkdir()

    # One employee has 10 hours available and no existing allocations.
    pd.DataFrame([
        {"employee_id": "E1", "role_id": "R1", "status": "active"}
    ]).to_csv(raw / "Employee.csv", index=False)

    pd.DataFrame([
        {"skill_id": "S1", "skill_name": "Python", "active": True}
    ]).to_csv(raw / "Skill.csv", index=False)

    pd.DataFrame([
        {
            "employee_id": "E1",
            "skill_id": "S1",
            "proficiency": 3,
            "last_verified_date": "2026-10-01",
            "valid_until": "2027-10-01",
        }
    ]).to_csv(raw / "EmployeeSkill.csv", index=False)

    pd.DataFrame([
        {
            "demand_id": "D1",
            "project_id": "P1",
            "role_id": "R1",
            "skill_id": "S1",
            "period": "2026W45",
            "required_hours": 8,
            "minimum_proficiency": 3,
            "status": "planned",
        },
        {
            "demand_id": "D2",
            "project_id": "P2",
            "role_id": "R1",
            "skill_id": "S1",
            "period": "2026W45",
            "required_hours": 7,
            "minimum_proficiency": 3,
            "status": "planned",
        },
    ]).to_csv(raw / "DemandPlan.csv", index=False)

    pd.DataFrame(columns=[
        "allocation_id", "employee_id", "project_id",
        "demand_id", "period", "allocated_hours"
    ]).to_csv(raw / "Allocation.csv", index=False)

    pd.DataFrame([
        {
            "availability_id": "A1",
            "employee_id": "E1",
            "period": "2026W45",
            "weekly_capacity_hours": 10,
            "leave_hours": 0,
            "available_hours": 10,
        }
    ]).to_csv(raw / "Availability.csv", index=False)

    monkeypatch.setattr(bl, "RAW_DIR", raw)
    monkeypatch.setattr(bl, "PROCESSED_DIR", processed)

    result = bl.calculate_skill_gaps().sort_values("demand_id")

    assert result["demand_id"].tolist() == ["D1", "D2"]
    assert result["qualified_remaining_hours"].tolist() == [8, 2]
    assert result["qualified_remaining_hours"].sum() == 10
    assert result["uncovered_hours"].tolist() == [8, 7]
    assert (processed / "GapAnalysis.csv").exists()



def test_scarcer_demand_receives_capacity_first(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw.mkdir()
    processed.mkdir()

    # Two employees share the same role and period.
    # E1 has both skills; E2 has only S2.
    pd.DataFrame([
        {"employee_id": "E1", "role_id": "R1", "status": "active"},
        {"employee_id": "E2", "role_id": "R1", "status": "active"},
    ]).to_csv(raw / "Employee.csv", index=False)

    pd.DataFrame([
        {"skill_id": "S1", "skill_name": "RareSkill", "active": True},
        {"skill_id": "S2", "skill_name": "CommonSkill", "active": True},
    ]).to_csv(raw / "Skill.csv", index=False)

    pd.DataFrame([
        {
            "employee_id": "E1",
            "skill_id": "S1",
            "proficiency": 3,
            "last_verified_date": "2026-10-01",
            "valid_until": "2027-10-01",
        },
        {
            "employee_id": "E1",
            "skill_id": "S2",
            "proficiency": 3,
            "last_verified_date": "2026-10-01",
            "valid_until": "2027-10-01",
        },
        {
            "employee_id": "E2",
            "skill_id": "S2",
            "proficiency": 3,
            "last_verified_date": "2026-10-01",
            "valid_until": "2027-10-01",
        },
    ]).to_csv(raw / "EmployeeSkill.csv", index=False)

    # D1 is earlier by ID but only E1 qualifies.
    # D2 has two qualified employees.
    pd.DataFrame([
        {
            "demand_id": "D1",
            "project_id": "P1",
            "role_id": "R1",
            "skill_id": "S1",
            "period": "2026W45",
            "required_hours": 8,
            "minimum_proficiency": 3,
            "status": "planned",
        },
        {
            "demand_id": "D2",
            "project_id": "P2",
            "role_id": "R1",
            "skill_id": "S2",
            "period": "2026W45",
            "required_hours": 8,
            "minimum_proficiency": 3,
            "status": "planned",
        },
    ]).to_csv(raw / "DemandPlan.csv", index=False)

    pd.DataFrame(columns=[
        "allocation_id", "employee_id", "project_id",
        "demand_id", "period", "allocated_hours",
    ]).to_csv(raw / "Allocation.csv", index=False)

    pd.DataFrame([
        {
            "availability_id": "A1",
            "employee_id": "E1",
            "period": "2026W45",
            "weekly_capacity_hours": 10,
            "leave_hours": 0,
            "available_hours": 10,
        },
        {
            "availability_id": "A2",
            "employee_id": "E2",
            "period": "2026W45",
            "weekly_capacity_hours": 10,
            "leave_hours": 0,
            "available_hours": 10,
        },
    ]).to_csv(raw / "Availability.csv", index=False)

    monkeypatch.setattr(bl, "RAW_DIR", raw)
    monkeypatch.setattr(bl, "PROCESSED_DIR", processed)

    result = bl.calculate_skill_gaps().set_index("demand_id")

    assert result.loc["D1", "qualified_remaining_hours"] == 8
    assert result.loc["D2", "qualified_remaining_hours"] == 8
    assert result["qualified_remaining_hours"].sum() == 16


def test_scarcity_order_is_deterministic():
    demand = pd.DataFrame([
        {
            "demand_id": "D2",
            "period": "2026W45",
            "eligible_employee_count": 2,
        },
        {
            "demand_id": "D1",
            "period": "2026W45",
            "eligible_employee_count": 1,
        },
        {
            "demand_id": "D3",
            "period": "2026W45",
            "eligible_employee_count": 2,
        },
    ])

    ordered = demand.sort_values(
        ["period", "eligible_employee_count", "demand_id"],
        kind="stable",
    )

    assert ordered["demand_id"].tolist() == ["D1", "D2", "D3"]



def test_reservations_never_exceed_shared_employee_capacity(
    tmp_path, monkeypatch
):
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw.mkdir()
    processed.mkdir()

    pd.DataFrame([
        {"employee_id": "E1", "role_id": "R1", "status": "active"}
    ]).to_csv(raw / "Employee.csv", index=False)

    pd.DataFrame([
        {"skill_id": "S1", "skill_name": "Python", "active": True}
    ]).to_csv(raw / "Skill.csv", index=False)

    pd.DataFrame([
        {
            "employee_id": "E1",
            "skill_id": "S1",
            "proficiency": 3,
            "last_verified_date": "2026-10-01",
            "valid_until": "2027-10-01",
        }
    ]).to_csv(raw / "EmployeeSkill.csv", index=False)

    pd.DataFrame([
        {
            "demand_id": "D1",
            "project_id": "P1",
            "role_id": "R1",
            "skill_id": "S1",
            "period": "2026W45",
            "required_hours": 8,
            "minimum_proficiency": 3,
            "status": "planned",
        },
        {
            "demand_id": "D2",
            "project_id": "P2",
            "role_id": "R1",
            "skill_id": "S1",
            "period": "2026W45",
            "required_hours": 7,
            "minimum_proficiency": 3,
            "status": "planned",
        },
        {
            "demand_id": "D3",
            "project_id": "P3",
            "role_id": "R1",
            "skill_id": "S1",
            "period": "2026W45",
            "required_hours": 6,
            "minimum_proficiency": 3,
            "status": "planned",
        },
    ]).to_csv(raw / "DemandPlan.csv", index=False)

    pd.DataFrame(columns=[
        "allocation_id", "employee_id", "project_id",
        "demand_id", "period", "allocated_hours",
    ]).to_csv(raw / "Allocation.csv", index=False)

    pd.DataFrame([
        {
            "availability_id": "A1",
            "employee_id": "E1",
            "period": "2026W45",
            "weekly_capacity_hours": 10,
            "leave_hours": 0,
            "available_hours": 10,
        }
    ]).to_csv(raw / "Availability.csv", index=False)

    monkeypatch.setattr(bl, "RAW_DIR", raw)
    monkeypatch.setattr(bl, "PROCESSED_DIR", processed)

    gaps, ledger = bl.calculate_skill_gaps(return_reservations=True)

    assert gaps["demand_id"].nunique() == 3
    assert not ledger.empty

    totals = ledger.groupby(
        ["employee_id", "period"]
    )["reserved_hours"].sum()

    assert totals.loc[("E1", "2026W45")] == 10
    assert (ledger["reserved_hours"] >= 0).all()
    assert (ledger["reserved_hours"] <= 10).all()
