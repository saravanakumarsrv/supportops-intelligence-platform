"""
Lesson purpose:
This file converts analytics into business recommendations.

Why?
Recruiters like projects that go beyond charts.
The best analyst work ends with decisions and action.
"""
from __future__ import annotations
from kpi_engine import calculate_kpis, issue_type_summary, agent_performance_summary
from root_cause_analyzer import top_pain_points
from sla_analyzer import sla_summary_by_department

def generate_recommendations(df) -> list[dict]:
    kpis = calculate_kpis(df)
    dept_sla = sla_summary_by_department(df)
    issues = issue_type_summary(df)
    agents = agent_performance_summary(df)
    pain_points = top_pain_points(df)
    recommendations = []
    worst_dept = dept_sla.iloc[0]
    recommendations.append({"opportunity": f"Reduce SLA breaches in {worst_dept['department']}", "reason": f"{worst_dept['department']} has the highest SLA breach rate at {worst_dept['sla_breach_rate']}%.", "recommendation": "Review staffing, queue routing, and escalation rules for this department.", "impact": "High", "difficulty": "Medium"})
    top_issue = issues.iloc[0]
    recommendations.append({"opportunity": f"Reduce volume for {top_issue['issue_type']}", "reason": f"{top_issue['issue_type']} is the highest-volume issue type with {top_issue['total_tickets']} tickets.", "recommendation": "Create self-service help content, automation, or clearer customer communication for this issue.", "impact": "High", "difficulty": "Medium"})
    if kpis["negative_sentiment_rate"] > 20:
        recommendations.append({"opportunity": "Prioritize negative sentiment tickets", "reason": f"{kpis['negative_sentiment_rate']}% of tickets show negative customer sentiment.", "recommendation": "Route negative sentiment tickets to senior agents or trigger manager review.", "impact": "High", "difficulty": "Low"})
    overloaded_agent = agents.iloc[0]
    recommendations.append({"opportunity": f"Balance workload for agent {overloaded_agent['agent']}", "reason": f"{overloaded_agent['agent']} has the highest ticket count with {overloaded_agent['total_tickets']} tickets.", "recommendation": "Redistribute tickets or adjust assignment rules to reduce workload imbalance.", "impact": "Medium", "difficulty": "Low"})
    top_pain = pain_points.iloc[0]
    recommendations.append({"opportunity": f"Fix root cause: {top_pain['issue_type']} in {top_pain['department']}", "reason": f"This area has {top_pain['high_risk_tickets']} high-risk tickets and {top_pain['sla_breaches']} SLA breaches.", "recommendation": "Run a focused process improvement review for this department and issue combination.", "impact": "High", "difficulty": "Medium"})
    return recommendations
