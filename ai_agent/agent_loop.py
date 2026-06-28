from __future__ import annotations

import os
from typing import Any

import pandas as pd

from ai_agent.briefing_agent import generate_daily_briefing
from kpi_engine import calculate_kpis, issue_type_summary
from risk_scoring import add_risk_score, top_high_risk_tickets
from root_cause_analyzer import top_pain_points
from sla_analyzer import sla_summary_by_department


def _dataframe_records(df: pd.DataFrame, max_rows: int = 10) -> list[dict[str, Any]]:
    return df.head(max_rows).to_dict(orient="records")


def _format_manager_briefing(briefing: dict) -> str:
    sections = briefing.get("briefing_sections", {})
    lines = [
        "Daily SupportOps AutoPilot Briefing",
        "",
        "Executive Summary:",
        sections.get("executive_summary", ""),
        "",
        "SLA Risk:",
        sections.get("sla_risk", ""),
        "",
        "Customer Sentiment Risk:",
        sections.get("customer_sentiment_risk", ""),
        "",
        "Top Issue Risk:",
        sections.get("top_issue_risk", ""),
        "",
        "Workload Risk:",
        sections.get("workload_risk", ""),
        "",
        "Recommended Actions:",
    ]

    for idx, action in enumerate(briefing.get("recommended_actions", []), start=1):
        lines.append(f"{idx}. {action}")

    return "\n".join(lines).strip()


def _detect_mode(briefing: dict, gemini_enabled: bool) -> str:
    if not gemini_enabled:
        return "fallback"

    trace = briefing.get("agent_trace", [])
    if any(
        "Gemini briefing failed" in step or "Used fallback briefing mode" in step
        for step in trace
    ):
        return "fallback"

    return "gemini"


def run_supportops_agent_loop(
    df: pd.DataFrame,
    user_question: str | None = None,
    max_steps: int = 5,
) -> dict[str, Any]:
    agent_trace: list[str] = []

    if df is None or df.empty:
        return {
            "status": "error",
            "mode": "fallback",
            "agent_trace": ["No support ticket data available."],
            "findings": {},
            "manager_briefing": "",
            "recommended_actions": [],
        }

    gemini_enabled = bool(os.getenv("GEMINI_API_KEY"))
    agent_trace.append(f"Loaded support ticket dataset with {len(df):,} rows.")

    if user_question:
        agent_trace.append(f"Received user question: {user_question}")

    scored_df = df.copy()
    if "escalation_risk_score" not in scored_df.columns or "risk_level" not in scored_df.columns:
        agent_trace.append("Calculated escalation risk scores and risk levels using existing scoring logic.")
        scored_df = add_risk_score(scored_df)
    else:
        agent_trace.append("Support dataset already contains risk scoring.")

    agent_trace.append("Computed SLA status and department-level SLA summary.")
    sla_by_department = sla_summary_by_department(scored_df)

    agent_trace.append("Calculated executive support KPIs and issue-type summary.")
    kpis = calculate_kpis(scored_df)
    issue_summary = issue_type_summary(scored_df)

    agent_trace.append("Identified top high-risk tickets and root-cause pain points.")
    high_risk = top_high_risk_tickets(scored_df)
    pain_points = top_pain_points(scored_df)

    if gemini_enabled:
        agent_trace.append("Gemini key detected; generating final manager briefing with Gemini-enabled briefing agent.")
    else:
        agent_trace.append("Gemini key not found; using deterministic fallback briefing logic.")

    briefing = generate_daily_briefing(scored_df)
    mode = _detect_mode(briefing, gemini_enabled)

    if mode == "fallback":
        agent_trace.append("AutoPilot is running in fallback mode.")
    else:
        agent_trace.append("AutoPilot completed using Gemini.")

    manager_briefing = _format_manager_briefing(briefing)
    recommended_actions = briefing.get("recommended_actions", [])

    findings = {
        "kpis": kpis,
        "sla_by_department": sla_by_department.to_dict(orient="records"),
        "issue_type_summary": issue_summary.to_dict(orient="records"),
        "top_high_risk_tickets": _dataframe_records(high_risk, max_rows=10),
        "top_pain_points": _dataframe_records(pain_points, max_rows=10),
    }

    if user_question:
        findings["user_question"] = user_question

    agent_trace.extend(briefing.get("agent_trace", []))

    return {
        "status": "success",
        "mode": mode,
        "agent_trace": agent_trace,
        "findings": findings,
        "manager_briefing": manager_briefing,
        "recommended_actions": recommended_actions,
    }
