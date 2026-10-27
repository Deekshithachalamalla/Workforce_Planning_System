
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
TRUTH = ROOT / "data" / "ground_truth" / "ground_truth.csv"

st.set_page_config(
    page_title="Workforce Planning System",
    page_icon="📊",
    layout="wide",
)

st.title("Workforce Demand & Skill Gap Analysis")
st.caption(
    "Workforce capacity, project demand, utilization risks, "
    "and hiring or training decisions."
)


def load_csv(path):
    if not path.exists():
        return None
    return pd.read_csv(path)


employees = load_csv(RAW / "Employee.csv")
projects = load_csv(RAW / "Project.csv")
demand = load_csv(RAW / "DemandPlan.csv")
utilization = load_csv(PROCESSED / "utilization.csv")
gaps = load_csv(PROCESSED / "GapAnalysis.csv")
findings = load_csv(PROCESSED / "anomaly_findings.csv")
truth = load_csv(TRUTH)

required = {
    "Employees": employees,
    "Projects": projects,
    "Demand plans": demand,
    "Utilization results": utilization,
    "Gap analysis": gaps,
}

missing = [name for name, data in required.items() if data is None]

if missing:
    st.error(
        "Some files are missing: "
        + ", ".join(missing)
        + ". Run the data-generation and business-logic scripts first."
    )
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")

periods = sorted(demand["period"].dropna().unique().tolist())
selected_period = st.sidebar.selectbox(
    "Planning period",
    ["All periods"] + periods,
)

filtered_utilization = utilization.copy()
filtered_gaps = gaps.copy()

if selected_period != "All periods":
    filtered_utilization = filtered_utilization[
        filtered_utilization["period"] == selected_period
    ]
    filtered_gaps = filtered_gaps[
        filtered_gaps["period"] == selected_period
    ]

# KPI calculations
total_employees = len(employees)
total_projects = len(projects)

total_demand = filtered_gaps["required_hours"].sum()
total_assigned = filtered_gaps["assigned_hours"].sum()
total_uncovered = filtered_gaps["uncovered_hours"].sum()

available_hours = filtered_utilization["available_hours"].sum()
allocated_hours = filtered_utilization["total_allocated_hours"].sum()

overall_utilization = (
    allocated_hours / available_hours * 100
    if available_hours > 0
    else 0
)

overallocated = (
    filtered_utilization["utilization_status"] == "overallocated"
).sum()

st.subheader("Workforce overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Employees", f"{total_employees:,}")
c2.metric("Projects", f"{total_projects:,}")
c3.metric("Overall utilization", f"{overall_utilization:.1f}%")
c4.metric("Uncovered demand", f"{total_uncovered:,.0f} hours")

c5, c6, c7 = st.columns(3)

c5.metric("Demand", f"{total_demand:,.0f} hours")
c6.metric("Assigned", f"{total_assigned:,.0f} hours")
c7.metric("Overallocated employee-weeks", f"{overallocated:,}")

st.divider()

# Demand and allocation chart
st.subheader("Demand versus assigned hours")

demand_chart = filtered_gaps[
    ["period", "required_hours", "assigned_hours"]
].groupby("period", as_index=False).sum()

if not demand_chart.empty:
    demand_chart = demand_chart.melt(
        id_vars="period",
        value_vars=["required_hours", "assigned_hours"],
        var_name="measure",
        value_name="hours",
    )

    fig = px.line(
        demand_chart,
        x="period",
        y="hours",
        color="measure",
        markers=True,
        title="Weekly demand and allocated hours",
    )
    st.plotly_chart(fig, use_container_width=True)

# Utilization distribution
st.subheader("Employee utilization")

fig_util = px.histogram(
    filtered_utilization,
    x="utilization_pct",
    nbins=20,
    title="Distribution of weekly utilization",
    labels={"utilization_pct": "Utilization (%)"},
)
st.plotly_chart(fig_util, use_container_width=True)

# Gap analysis
st.subheader("Skill gap analysis")

if "skill_name" in filtered_gaps.columns:
    skill_summary = (
        filtered_gaps.groupby("skill_name", as_index=False)
        ["uncovered_hours"]
        .sum()
        .sort_values("uncovered_hours", ascending=False)
        .head(15)
    )

    fig_gaps = px.bar(
        skill_summary,
        x="uncovered_hours",
        y="skill_name",
        orientation="h",
        title="Top 15 skills by uncovered demand",
        labels={
            "uncovered_hours": "Uncovered hours",
            "skill_name": "Skill",
        },
    )
    st.plotly_chart(fig_gaps, use_container_width=True)

    st.dataframe(
        filtered_gaps.sort_values(
            "uncovered_hours", ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning("Skill names are not available in the gap analysis output.")

# Exceptions
st.subheader("Anomaly findings")

if findings is not None and not findings.empty:
    st.metric("Detected findings", len(findings))

    counts = findings["issue_type"].value_counts().rename_axis(
        "issue_type"
    ).reset_index(name="count")

    fig_anomalies = px.bar(
        counts,
        x="issue_type",
        y="count",
        title="Detected findings by anomaly type",
    )
    st.plotly_chart(fig_anomalies, use_container_width=True)

    st.dataframe(findings, use_container_width=True, hide_index=True)
else:
    st.info(
        "No anomaly findings file is available yet. "
        "Run the anomaly detector to generate it."
    )

if truth is not None:
    st.caption(
        f"Ground-truth reference contains {len(truth)} labelled cases. "
        "Labels are kept separate from normal input features."
    )

# Download reports
st.subheader("Download reports")

download_columns = st.columns(3)

with download_columns[0]:
    st.download_button(
        "Download gap analysis",
        filtered_gaps.to_csv(index=False).encode("utf-8"),
        file_name="gap_analysis.csv",
        mime="text/csv",
    )

with download_columns[1]:
    st.download_button(
        "Download utilization",
        filtered_utilization.to_csv(index=False).encode("utf-8"),
        file_name="utilization.csv",
        mime="text/csv",
    )

with download_columns[2]:
    if findings is not None:
        st.download_button(
            "Download anomalies",
            findings.to_csv(index=False).encode("utf-8"),
            file_name="anomaly_findings.csv",
            mime="text/csv",
        )

st.caption(
    "Prototype decision-support system. Recommendations and "
    "metrics should be validated before operational use."
)
