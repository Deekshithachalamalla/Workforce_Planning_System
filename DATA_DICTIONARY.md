# Workforce Planning System â€” Data Dictionary

## 1. Overview

This document defines the raw data entities used by the Workforce Planning System, including their fields, expected data types, primary keys, foreign-key relationships, and validation rules.

The project uses synthetic workforce data to analyze employee capacity, project demand, resource allocation, skill gaps, and data-quality anomalies.

## 2. Data Type Conventions

| Type | Description |
|---|---|
| String | Text identifier or descriptive value |
| Integer | Whole number |
| Float | Numeric value that may contain decimals |
| Boolean | True/false value |
| Date | Calendar date |
| Period | Planning period, represented as a string |

The types below are expected logical types. Confirm them against the generator code and actual CSV values before treating them as enforced database types.

## 3. Master Data Entities

### 3.1 Employee

**Source:** `data/raw/Employee.csv`

**Purpose:** Stores employee identity, employment details, and role assignment.

| Field | Expected type | Key | Description |
|---|---|---|---|
| employee_id | String | Primary key | Unique employee identifier |
| employee_name | String | â€” | Employee name |
| role_id | String | Foreign key | References Role |
| employment_type | String | â€” | Employment category |
| weekly_hours | Float | â€” | Contracted weekly working hours |
| status | String | â€” | Employee lifecycle or employment status |
| hire_date | Date | â€” | Employee hire date |

**Validation rules**
- `employee_id` must be unique and non-empty.
- `role_id` must reference an existing role.
- `weekly_hours` must be non-negative.
- `hire_date` must be a valid date.
- Employment type and status should use documented allowed values.

### 3.2 Role

**Source:** `data/raw/Role.csv`

**Purpose:** Defines workforce job roles.

| Field | Expected type | Key | Description |
|---|---|---|---|
| role_id | String | Primary key | Unique role identifier |
| role_name | String | â€” | Role name |
| active | Boolean | â€” | Indicates whether the role is active |

**Validation rules**
- `role_id` must be unique.
- `role_name` must not be empty.
- `active` must contain a valid Boolean value.

### 3.3 Skill

**Source:** `data/raw/Skill.csv`

**Purpose:** Defines the skills used to match employee capabilities to project demand.

| Field | Expected type | Key | Description |
|---|---|---|---|
| skill_id | String | Primary key | Unique skill identifier |
| skill_name | String | â€” | Skill name |
| active | Boolean | â€” | Indicates whether the skill is active |
| validity_days | Integer | â€” | Skill validity or verification period in days |

**Validation rules**
- `skill_id` must be unique.
- `skill_name` must not be empty.
- `validity_days` must follow the project's configured rules and must not be negative.

### 3.4 Project

**Source:** `data/raw/Project.csv`

**Purpose:** Stores project details and project lifecycle dates.

| Field | Expected type | Key | Description |
|---|---|---|---|
| project_id | String | Primary key | Unique project identifier |
| project_name | String | â€” | Project name |
| project_manager_id | String | Optional/unverified | Project manager identifier |
| status | String | â€” | Project lifecycle status |
| start_date | Date | â€” | Project start date |
| end_date | Date | â€” | Project end date |

**Validation rules**
- `project_id` must be unique.
- `project_name` must not be empty.
- Project dates must be valid.
- `end_date` must not precede `start_date`.
- The relationship for `project_manager_id` must be documented if manager records are available.

### 3.5 EmployeeSkill

**Source:** `data/raw/EmployeeSkill.csv`

**Purpose:** Links employees to skills and records proficiency and verification information.

| Field | Expected type | Key | Description |
|---|---|---|---|
| employee_skill_id | String | Primary key | Unique employee-skill record identifier |
| employee_id | String | Foreign key | References Employee |
| skill_id | String | Foreign key | References Skill |
| proficiency | Integer or Float | â€” | Employee proficiency level |
| last_verified_date | Date | â€” | Date the skill was last verified |
| valid_until | Date | â€” | Date until which the skill is considered valid |
| claimed_current | Boolean | â€” | Indicates whether the skill is claimed to be current |

**Validation rules**
- `employee_skill_id` must be unique.
- Employee and skill references must exist.
- Proficiency must follow the defined proficiency scale.
- Verification and validity dates must be valid.
- A skill claimed as current should be checked against its verification and expiry rules.

## 4. Transaction Data Entities

### 4.1 DemandPlan

**Source:** `data/raw/DemandPlan.csv`

**Purpose:** Records workforce demand by project, role, skill, and planning period.

| Field | Expected type | Key | Description |
|---|---|---|---|
| demand_id | String | Primary key | Unique demand record identifier |
| project_id | String | Foreign key | References Project |
| role_id | String | Foreign key | References Role |
| skill_id | String | Foreign key | References Skill |
| period | String | â€” | Demand planning period |
| required_hours | Float | â€” | Required workforce hours |
| minimum_proficiency | Integer or Float | â€” | Minimum required skill proficiency |
| status | String | â€” | Demand lifecycle status |

**Validation rules**
- `demand_id` must be unique.
- Project, role, and skill references must exist.
- `required_hours` must be non-negative.
- `period` must follow the configured planning-period format.
- Demand status and minimum proficiency must follow documented rules.
- Duplicate business demand records should be detected using the appropriate project, role, skill, and period combination.

### 4.2 Allocation

**Source:** `data/raw/Allocation.csv`

**Purpose:** Records employee assignments to projects and demand records.

| Field | Expected type | Key | Description |
|---|---|---|---|
| allocation_id | String | Primary key | Unique allocation identifier |
| employee_id | String | Foreign key | References Employee |
| project_id | String | Foreign key | References Project |
| demand_id | String | Foreign key | References DemandPlan |
| period | String | â€” | Allocation planning period |
| allocated_hours | Float | â€” | Hours assigned to the project |

**Validation rules**
- `allocation_id` must be unique.
- Employee, project, and demand references must exist.
- The allocation project should match the project referenced by the demand record.
- Allocation hours must be non-negative.
- Allocated hours must be compared with employee availability.
- Overlapping assignments must be checked for each employee and period.

### 4.3 Availability

**Source:** `data/raw/Availability.csv`

**Purpose:** Records employee working capacity and leave for each planning period.

| Field | Expected type | Key | Description |
|---|---|---|---|
| availability_id | String | Primary key | Unique availability record identifier |
| employee_id | String | Foreign key | References Employee |
| period | String | â€” | Availability planning period |
| weekly_capacity_hours | Float | â€” | Weekly capacity before leave |
| leave_hours | Float | â€” | Leave hours in the period |
| available_hours | Float | â€” | Capacity remaining after leave |

**Validation rules**
- `availability_id` must be unique.
- Employee references must exist.
- Capacity, leave, and available hours must be non-negative.
- `leave_hours` must not exceed the applicable capacity.
- The expected reconciliation is `available_hours = weekly_capacity_hours - leave_hours`, subject to the project's calculation rules.
- Part-time capacity must be reflected correctly.

### 4.4 Training

**Source:** `data/raw/Training.csv`

**Purpose:** Records planned employee training activities that may help address skill gaps.

| Field | Expected type | Key | Description |
|---|---|---|---|
| training_id | String | Primary key | Unique training record identifier |
| employee_id | String | Foreign key | References Employee |
| skill_id | String | Foreign key | References Skill |
| period | String | â€” | Planned training period |
| planned_hours | Float | â€” | Planned training duration |
| status | String | â€” | Training lifecycle status |

**Validation rules**
- `training_id` must be unique.
- Employee and skill references must exist.
- `planned_hours` must be non-negative.
- Training period and status must follow the documented rules.
- Training should not automatically be treated as completed skill proficiency without supporting evidence.

## 5. Derived Data Entity

### 5.1 GapAnalysis

**Expected output:** `data/processed/GapAnalysis.csv`

**Purpose:** Summarizes workforce demand that remains uncovered after accounting for relevant resource assignments and availability.

This is a derived output rather than one of the nine raw input tables. Its exact fields, data types, and record granularity must be confirmed from the generated CSV.

**Validation requirements**
- Every reported gap should be traceable to the relevant demand records.
- Gap calculations should use consistent periods and units.
- Covered and uncovered demand should reconcile according to the business rules.
- Re-running the analysis on unchanged inputs should produce consistent results.

## 6. Relationships and Cardinality

| Parent entity | Child entity | Expected relationship |
|---|---|---|
| Role | Employee | One-to-many |
| Employee | EmployeeSkill | One-to-many |
| Skill | EmployeeSkill | One-to-many |
| Project | DemandPlan | One-to-many |
| Role | DemandPlan | One-to-many |
| Skill | DemandPlan | One-to-many |
| Employee | Allocation | One-to-many |
| Project | Allocation | One-to-many |
| DemandPlan | Allocation | One-to-many |
| Employee | Availability | One-to-many across periods |
| Employee | Training | One-to-many |
| Skill | Training | One-to-many |

Employee and Skill have a many-to-many relationship through EmployeeSkill.

The exact constraints, optional relationships, and uniqueness rules should be confirmed against the generator and validation code.

## 7. Units and Business Rules

| Measure | Unit | Rule |
|---|---|---|
| required_hours | Hours | Demand must be non-negative |
| allocated_hours | Hours | Assigned work must be non-negative |
| weekly_capacity_hours | Hours per week | Must respect employment capacity |
| leave_hours | Hours per period | Must not exceed applicable capacity |
| available_hours | Hours per period | Capacity after applicable leave |
| planned_hours | Hours | Planned training time |
| proficiency | Configured proficiency scale | Must meet the documented allowed range |
| validity_days | Days | Used according to skill validity rules |

Planning periods must use one consistent format throughout the dataset.

## 8. Data Quality and Anomaly Checks

The system should detect and report:

1. Duplicate primary keys.
2. Invalid foreign-key references.
3. Missing required values.
4. Invalid dates and planning periods.
5. Allocations exceeding employee availability.
6. Employees assigned to overlapping projects.
7. Stale skills incorrectly treated as current.
8. Duplicate demand records that cause double counting.
9. Capacity and demand reconciliation errors.
10. Untraceable or inconsistent calculated gaps.

Ground-truth anomaly labels must remain separate from the ordinary source data used for detection and evaluation.

## 9. Implementation Notes

- The raw dataset contains nine CSV tables representing the master and transaction entities.
- GapAnalysis is a derived output.
- Processed anomaly findings and ground-truth evaluation are analytical outputs, not additional core business entities.
- Expected data types and relationship rules in this document must be verified against the implementation.
- Allowed values, required-versus-optional fields, and database-level constraints should be documented from the actual generator and validation code.

## 10. Completion Status

This data dictionary documents the observed raw CSV column names and expected business meaning. Final verification requires checking the generator, business logic, validation rules, and the actual GapAnalysis output schema.

## 11. Processed Output Data Dictionary

### 11.1 GapAnalysis

**Source:** `data/processed/GapAnalysis.csv`

**Purpose:** Identifies uncovered project demand and provides potential workforce planning actions.

| Field | Expected type | Description |
|---|---|---|
| gap_id | String | Identifier for the gap-analysis record |
| demand_id | String | Related demand record |
| project_id | String | Related project |
| role_id | String | Required workforce role |
| skill_id | String | Required skill |
| period | String | Planning period |
| required_hours | Float | Total required demand hours |
| assigned_hours | Float | Hours assigned to the demand |
| uncovered_hours | Float | Demand hours that remain uncovered |
| qualified_remaining_hours | Float | Remaining qualified capacity considered by the analysis |
| recommended_action | String | Suggested action for addressing the gap |
| skill_name | String | Descriptive name of the required skill |

**Validation rules**
- `gap_id` should uniquely identify a gap record.
- `demand_id`, `project_id`, `role_id`, and `skill_id` should trace back to valid source records.
- Hour values must be non-negative.
- `uncovered_hours` should reconcile with required and assigned hours according to the implementation's business rules.
- Recommendations should be traceable to the demand gap and the assumptions used.

### 11.2 Utilization

**Source:** `data/processed/utilization.csv`

**Purpose:** Summarizes employee capacity, allocations, remaining capacity, and utilization by planning period.

| Field | Expected type | Description |
|---|---|---|
| availability_id | String | Related availability record |
| employee_id | String | Employee identifier |
| period | String | Planning period |
| weekly_capacity_hours | Float | Weekly capacity before leave |
| leave_hours | Float | Leave hours |
| available_hours | Float | Available capacity after leave |
| role_id | String | Employee's role |
| employment_type | String | Employee employment category |
| total_allocated_hours | Float | Total hours allocated in the period |
| capacity_balance_hours | Float | Capacity remaining after allocations |
| utilization_pct | Float | Utilization percentage |
| utilization_status | String | Utilization classification |

**Validation rules**
- Availability and employee references must be valid.
- Capacity and allocation values must use consistent units and periods.
- Capacity balance should reconcile with available hours and total allocated hours.
- Utilization percentage must follow the formula defined in the business logic.
- Utilization status should follow documented thresholds.

### 11.3 Anomaly Findings

**Source:** `data/processed/anomaly_findings.csv`

**Purpose:** Records detected data-quality or workforce-planning issues.

| Field | Expected type | Description |
|---|---|---|
| issue_type | String | Category of detected issue |
| record_id | String | Identifier of the affected record |
| explanation | String | Explanation of the detected issue |

**Validation rules**
- `issue_type` should use documented issue categories.
- `record_id` should identify the affected source record or business record.
- Each finding should have an understandable explanation.
- Repeated findings should be evaluated according to the intended reporting granularity.

### 11.4 Ground Truth Evaluation

**Source:** `data/processed/ground_truth_evaluation.csv`

**Purpose:** Compares expected labelled anomalies against the results of anomaly detection.

| Field | Expected type | Description |
|---|---|---|
| issue_type | String | Expected anomaly category |
| record_id | String | Identifier of the labelled record |
| detected | Boolean | Indicates whether the labelled issue was detected |

**Validation rules**
- Issue categories and record identifiers should match the ground-truth definitions.
- `detected` should contain a valid Boolean value.
- Evaluation data should remain separate from ordinary source data.
- Detection coverage alone should not be reported as overall accuracy, precision, or recall.

## 12. Ground Truth Input

**Source:** `data/ground_truth/ground_truth.csv`

This file contains expected anomaly labels used to evaluate the detection rules.

The exact fields in this file should be documented by inspecting its header. The ground truth must remain separate from the source records used by the detection process to avoid evaluation leakage.

## 13. Final Verification Checklist

- [ ] Confirm actual field data types from the generation code and CSV values.
- [ ] Document allowed values for employment type, lifecycle status, proficiency, and issue type.
- [ ] Confirm primary-key uniqueness and foreign-key relationships.
- [ ] Verify availability and utilization calculations.
- [ ] Verify demand-gap reconciliation.
- [ ] Confirm ground-truth columns and anomaly labels.
- [ ] Document the exact rules used to generate recommendations.

## 14. Ground Truth Data Dictionary

**Source:** `data/ground_truth/ground_truth.csv`

**Purpose:** Stores the expected outcomes for known anomaly scenarios so that the system's detection results can be evaluated.

| Field | Expected type | Description |
|---|---|---|
| issue_id | String | Unique identifier for the expected issue |
| issue_type | String | Category of expected anomaly |
| entity_type | String | Type of entity affected by the issue |
| record_id | String | Identifier of the affected record |
| expected_decision | String | Expected outcome or decision for the issue |

### Validation rules

- `issue_id` should be unique and non-empty.
- `issue_type` should use the documented anomaly categories.
- `entity_type` should identify a valid entity type.
- `record_id` should identify the relevant source record.
- `expected_decision` should use documented values.
- Ground-truth labels must be kept separate from the data used to detect anomalies.

## 15. Data Dictionary Coverage

This document covers the nine raw CSV entities, the derived `GapAnalysis` output, and the supporting utilization, anomaly findings, ground-truth evaluation, and ground-truth input files.

Column names were obtained from the CSV headers. Data types, allowed values, nullability, and relationship constraints are documented as expected rules and must be verified against the actual Python implementation before being described as enforced constraints.
