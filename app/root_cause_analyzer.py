"""
Lesson purpose:
This file finds root-cause patterns.

Why?
A dashboard tells us what is happening.
Root-cause analysis helps explain why it is happening.
"""
from __future__ import annotations
import pandas as pd
from risk_scoring import add_risk_score

def root_cause_summary(df: pd.DataFrame) -> pd.DataFrame:
    df = add_risk_score(df)
    return df.groupby(["department", "issue_type"], as_index=False).agg(total_tickets=("ticket_id", "count"), sla_breaches=("sla_breached", "sum"), high_risk_tickets=("risk_level", lambda x: (x == "High").sum()), avg_risk_score=("escalation_risk_score", "mean"), avg_customer_rating=("customer_rating", "mean")).round(2).sort_values(["high_risk_tickets", "sla_breaches"], ascending=False)

def top_pain_points(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return root_cause_summary(df).head(n)
