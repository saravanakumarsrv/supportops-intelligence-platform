"""
Lesson purpose:
This file checks SLA performance.

Why?
SLA breach rate is one of the most important customer support KPIs.
It tells the business whether customers are being helped within promised time.
"""
from __future__ import annotations
import pandas as pd

def prepare_ticket_dates(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["created_at"] = pd.to_datetime(result["created_at"])
    result["sla_due_at"] = pd.to_datetime(result["sla_due_at"])
    result["closed_at"] = pd.to_datetime(result["closed_at"], errors="coerce")
    result["actual_resolution_hours"] = ((result["closed_at"] - result["created_at"]).dt.total_seconds() / 3600)
    return result

def add_sla_status(df: pd.DataFrame) -> pd.DataFrame:
    result = prepare_ticket_dates(df)
    analysis_date = pd.Timestamp("2026-01-01")
    statuses = []
    for _, row in result.iterrows():
        if pd.notna(row["closed_at"]):
            statuses.append("Breached" if row["closed_at"] > row["sla_due_at"] else "Met")
        else:
            statuses.append("Breached" if analysis_date > row["sla_due_at"] else "Open - On Track")
    result["sla_status"] = statuses
    result["sla_breached"] = result["sla_status"].eq("Breached")
    return result

def sla_summary_by_department(df: pd.DataFrame) -> pd.DataFrame:
    df = add_sla_status(df)
    return df.groupby("department", as_index=False).agg(total_tickets=("ticket_id", "count"), sla_breach_rate=("sla_breached", lambda x: x.mean() * 100), avg_resolution_hours=("actual_resolution_hours", "mean")).round(2).sort_values("sla_breach_rate", ascending=False)

def sla_summary_by_priority(df: pd.DataFrame) -> pd.DataFrame:
    df = add_sla_status(df)
    return df.groupby("priority", as_index=False).agg(total_tickets=("ticket_id", "count"), sla_breach_rate=("sla_breached", lambda x: x.mean() * 100), avg_resolution_hours=("actual_resolution_hours", "mean")).round(2).sort_values("sla_breach_rate", ascending=False)
