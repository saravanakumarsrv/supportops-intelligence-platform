"""
Lesson purpose:
This file calculates support KPIs.

Why?
KPIs translate raw ticket records into business language.
Managers do not want to read 3,000 rows. They want metrics.
"""
from __future__ import annotations
import pandas as pd
from risk_scoring import add_risk_score

def calculate_kpis(df: pd.DataFrame) -> dict:
    df = add_risk_score(df)
    return {
        "total_tickets": int(len(df)),
        "open_tickets": int(df["status"].eq("Open").sum()),
        "closed_tickets": int(df["status"].eq("Closed").sum()),
        "escalated_tickets": int(df["status"].eq("Escalated").sum()),
        "sla_breach_rate": round(df["sla_breached"].mean() * 100, 2),
        "avg_resolution_hours": round(df["actual_resolution_hours"].mean(), 2),
        "avg_customer_rating": round(df["customer_rating"].mean(), 2),
        "high_risk_tickets": int(df["risk_level"].eq("High").sum()),
        "negative_sentiment_rate": round(df["sentiment"].isin(["Negative", "Very Negative"]).mean() * 100, 2),
    }

def agent_performance_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = add_risk_score(df)
    return df.groupby("agent", as_index=False).agg(total_tickets=("ticket_id", "count"), avg_resolution_hours=("actual_resolution_hours", "mean"), sla_breach_rate=("sla_breached", lambda x: x.mean() * 100), avg_customer_rating=("customer_rating", "mean"), high_risk_tickets=("risk_level", lambda x: (x == "High").sum())).round(2).sort_values("total_tickets", ascending=False)

def issue_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = add_risk_score(df)
    return df.groupby("issue_type", as_index=False).agg(total_tickets=("ticket_id", "count"), sla_breach_rate=("sla_breached", lambda x: x.mean() * 100), avg_risk_score=("escalation_risk_score", "mean"), avg_customer_rating=("customer_rating", "mean")).round(2).sort_values("total_tickets", ascending=False)
