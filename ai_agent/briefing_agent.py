"""
Daily Support Briefing Agent

This agent analyzes the full support queue and generates a manager-ready briefing.
"""

from __future__ import annotations

import pandas as pd

from kpi_engine import calculate_kpis, agent_performance_summary, issue_type_summary
from risk_scoring import add_risk_score, top_high_risk_tickets
from root_cause_analyzer import top_pain_points
from sla_analyzer import sla_summary_by_department


def _safe_first_value(df: pd.DataFrame, column: str, default="N/A"):
    if df.empty or column not in df.columns:
        return default
    return df.iloc[0][column]


def identify_overloaded_agents(df: pd.DataFrame) -> pd.DataFrame:
    """Find agents carrying above-average ticket volume or high-risk workload."""
    agent_summary = agent_performance_summary(df)

    if agent_summary.empty:
        return agent_summary

    avg_ticket_count = agent_summary["total_tickets"].mean()
    avg_high_risk = agent_summary["high_risk_tickets"].mean()

    overloaded = agent_summary[
        (agent_summary["total_tickets"] > avg_ticket_count)
        | (agent_summary["high_risk_tickets"] > avg_high_risk)
    ].copy()

    overloaded["workload_reason"] = overloaded.apply(
        lambda row: (
            "High ticket volume and high-risk workload"
            if row["total_tickets"] > avg_ticket_count and row["high_risk_tickets"] > avg_high_risk
            else "High ticket volume"
            if row["total_tickets"] > avg_ticket_count
            else "High-risk workload"
        ),
        axis=1,
    )

    return overloaded.sort_values(
        ["high_risk_tickets", "total_tickets"], ascending=False
    )


def generate_daily_briefing(df: pd.DataFrame) -> dict:
    """Generate a manager-ready daily support operations briefing."""
    scored_df = add_risk_score(df)
    kpis = calculate_kpis(df)
    dept_sla = sla_summary_by_department(df)
    issue_summary = issue_type_summary(df)
    high_risk = top_high_risk_tickets(df, n=10)
    pain_points = top_pain_points(df, n=5)
    overloaded_agents = identify_overloaded_agents(df)

    worst_department = _safe_first_value(dept_sla, "department")
    worst_department_breach = _safe_first_value(dept_sla, "sla_breach_rate", 0)

    top_issue = _safe_first_value(issue_summary, "issue_type")
    top_issue_count = _safe_first_value(issue_summary, "total_tickets", 0)

    high_risk_count = int(scored_df["risk_level"].eq("High").sum())
    breached_count = int(scored_df["sla_breached"].sum())
    negative_count = int(scored_df["sentiment"].isin(["Negative", "Very Negative"]).sum())

    briefing_sections = {
        "executive_summary": (
            f"Today’s support queue contains {kpis['total_tickets']:,} tickets. "
            f"The SLA breach rate is {kpis['sla_breach_rate']}%, with {high_risk_count:,} high-risk tickets "
            f"and {negative_count:,} tickets showing negative customer sentiment."
        ),
        "sla_risk": (
            f"{worst_department} currently has the highest SLA breach rate at {worst_department_breach}%. "
            f"Total breached tickets in the selected data: {breached_count:,}."
        ),
        "customer_sentiment_risk": (
            f"{negative_count:,} tickets show negative or very negative sentiment. "
            "These should be prioritized because frustrated customers are more likely to escalate or churn."
        ),
        "top_issue_risk": (
            f"The highest-volume issue type is '{top_issue}' with {top_issue_count} tickets. "
            "High-volume issue types are strong candidates for self-service, automation, or process improvement."
        ),
        "workload_risk": (
            f"{len(overloaded_agents)} agents appear overloaded based on ticket volume or high-risk workload."
        ),
    }

    recommended_actions = []

    if kpis["sla_breach_rate"] >= 20:
        recommended_actions.append(
            "Escalate breached SLA tickets and review queue routing for the highest-breach department."
        )

    if high_risk_count > 0:
        recommended_actions.append(
            f"Review the top {min(10, high_risk_count)} high-risk tickets before normal queue work."
        )

    if negative_count > 0:
        recommended_actions.append(
            "Send proactive updates to customers with negative sentiment, especially when SLA is breached or close to breach."
        )

    if len(overloaded_agents) > 0:
        recommended_actions.append(
            "Rebalance ticket assignments from overloaded agents to agents with lighter queues."
        )

    recommended_actions.append(
        f"Investigate '{top_issue}' as a process improvement opportunity because it is the highest-volume issue."
    )

    agent_trace = [
        "Loaded support ticket dataset",
        "Validated available support operations fields",
        "Calculated executive support KPIs",
        "Checked SLA breach patterns by department",
        "Analyzed sentiment and escalation risk distribution",
        "Identified top high-risk tickets",
        "Identified overloaded agents",
        "Identified root-cause pain points",
        "Generated manager-ready daily action plan",
    ]

    return {
        "kpis": kpis,
        "briefing_sections": briefing_sections,
        "recommended_actions": recommended_actions,
        "top_high_risk_tickets": high_risk,
        "top_pain_points": pain_points,
        "overloaded_agents": overloaded_agents,
        "agent_trace": agent_trace,
    }


def generate_briefing_text(df: pd.DataFrame) -> str:
    """Create a copy-paste manager briefing as plain text."""
    briefing = generate_daily_briefing(df)
    sections = briefing["briefing_sections"]
    actions = briefing["recommended_actions"]

    action_text = "\n".join(
        [f"{idx}. {action}" for idx, action in enumerate(actions, start=1)]
    )

    return f"""
Daily SupportOps AI Briefing

Executive Summary:
{sections['executive_summary']}

SLA Risk:
{sections['sla_risk']}

Customer Sentiment Risk:
{sections['customer_sentiment_risk']}

Top Issue Risk:
{sections['top_issue_risk']}

Workload Risk:
{sections['workload_risk']}

Recommended Actions:
{action_text}
""".strip()
