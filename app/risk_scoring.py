"""
Lesson purpose:
This file creates an escalation risk score from 0 to 100.

Why?
Dashboards should not only show what happened.
A strong analyst project helps the business decide what to do next.
Risk scoring helps managers prioritize tickets before customers escalate.
"""
from __future__ import annotations
import pandas as pd
from sentiment_analyzer import sentiment_label
from sla_analyzer import add_sla_status

def priority_points(priority: str) -> int:
    return {"Low": 5, "Medium": 15, "High": 25, "Critical": 35}.get(priority, 0)

def sentiment_points(label: str) -> int:
    return {"Positive": 0, "Neutral": 5, "Negative": 15, "Very Negative": 25}.get(label, 0)

def sla_points(sla_status: str) -> int:
    return {"Met": 0, "Open - On Track": 5, "At Risk": 15, "Breached": 25}.get(sla_status, 0)

def add_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    result = add_sla_status(df)
    result["sentiment"] = result["customer_message"].apply(sentiment_label)
    scores = []
    for _, row in result.iterrows():
        score = 0
        score += priority_points(row["priority"])
        score += sentiment_points(row["sentiment"])
        score += sla_points(row["sla_status"])
        score += min(int(row["previous_contacts"]) * 5, 20)
        if row["status"] == "Escalated":
            score += 20
        if row["customer_rating"] <= 2:
            score += 10
        scores.append(min(score, 100))
    result["escalation_risk_score"] = scores
    result["risk_level"] = pd.cut(result["escalation_risk_score"], bins=[-1, 39, 69, 100], labels=["Low", "Medium", "High"]).astype(str)
    return result

def top_high_risk_tickets(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    df = add_risk_score(df)
    columns = ["ticket_id", "department", "issue_type", "priority", "agent", "status", "sla_status", "sentiment", "previous_contacts", "customer_rating", "escalation_risk_score", "customer_message"]
    return df[columns].sort_values("escalation_risk_score", ascending=False).head(n)
