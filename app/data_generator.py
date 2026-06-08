"""
Lesson purpose:
This file creates fake customer support tickets.

Why?
A data/BI/business analyst often cannot build dashboards without data.
When real company data is unavailable, we create realistic synthetic data to prove the workflow.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

RAW_DATA_PATH = Path("data/raw/support_tickets.csv")
DEPARTMENTS = ["Billing", "Technical Support", "Shipping", "Account Management", "Product Support"]
ISSUE_TYPES = ["Refund Delay", "Login Issue", "Late Delivery", "Account Verification", "Subscription Cancellation", "Bug Report", "Payment Failure", "Product Question"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
AGENTS = ["Ava", "Noah", "Mia", "Liam", "Priya", "David", "Sarah", "Ethan"]
CHANNELS = ["Email", "Chat", "Phone", "Web Form"]
NEGATIVE_MESSAGES = [
    "I have contacted support multiple times and nobody has helped me.",
    "This is very frustrating and I need this fixed immediately.",
    "I am tired of waiting for a response.",
    "This issue is affecting my work and I am unhappy.",
    "I want to cancel if this is not resolved today.",
]
NEUTRAL_MESSAGES = [
    "I need help with my account.",
    "Can you check the status of my request?",
    "I am having an issue and need assistance.",
    "Please help me understand what happened.",
    "I would like an update on my ticket.",
]
POSITIVE_MESSAGES = [
    "Thanks for helping me with this issue.",
    "The support team has been helpful so far.",
    "I appreciate the quick response.",
    "The issue was handled well.",
    "Thank you for the update.",
]

def random_date(start: datetime, end: datetime) -> datetime:
    total_days = (end - start).days
    return start + timedelta(days=random.randint(0, total_days))

def sla_hours_for_priority(priority: str) -> int:
    sla_map = {"Critical": 8, "High": 24, "Medium": 48, "Low": 72}
    return sla_map[priority]

def generate_ticket_data(records: int = 3000, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 12, 31)
    rows = []
    for i in range(1, records + 1):
        ticket_id = f"TKT-{i:05d}"
        department = random.choice(DEPARTMENTS)
        issue_type = random.choice(ISSUE_TYPES)
        priority = random.choices(PRIORITIES, weights=[0.25, 0.45, 0.23, 0.07])[0]
        agent = random.choice(AGENTS)
        channel = random.choice(CHANNELS)
        created_at = random_date(start_date, end_date)
        sla_due_at = created_at + timedelta(hours=sla_hours_for_priority(priority))
        base_resolution_hours = {"Low": random.randint(12, 90), "Medium": random.randint(8, 80), "High": random.randint(4, 60), "Critical": random.randint(2, 36)}[priority]
        if issue_type in ["Refund Delay", "Account Verification", "Bug Report"]:
            base_resolution_hours += random.randint(8, 36)
        if department in ["Billing", "Technical Support"]:
            base_resolution_hours += random.randint(4, 24)
        status = random.choices(["Closed", "Open", "Escalated"], weights=[0.72, 0.18, 0.10])[0]
        if status == "Open":
            closed_at = None
            resolution_hours = None
        else:
            closed_at = created_at + timedelta(hours=base_resolution_hours)
            resolution_hours = base_resolution_hours
        previous_contacts = random.choices([0, 1, 2, 3, 4, 5], weights=[0.45, 0.25, 0.14, 0.08, 0.05, 0.03])[0]
        message_type = random.choices(["positive", "neutral", "negative"], weights=[0.18, 0.52, 0.30])[0]
        if message_type == "positive":
            customer_message = random.choice(POSITIVE_MESSAGES)
            customer_rating = random.choice([4, 5])
        elif message_type == "neutral":
            customer_message = random.choice(NEUTRAL_MESSAGES)
            customer_rating = random.choice([3, 4])
        else:
            customer_message = random.choice(NEGATIVE_MESSAGES)
            customer_rating = random.choice([1, 2, 3])
        rows.append({"ticket_id": ticket_id, "customer_id": f"CUST-{random.randint(1000, 1999)}", "department": department, "issue_type": issue_type, "priority": priority, "agent": agent, "channel": channel, "created_at": created_at, "sla_due_at": sla_due_at, "closed_at": closed_at, "status": status, "resolution_hours": resolution_hours, "previous_contacts": previous_contacts, "customer_message": customer_message, "customer_rating": customer_rating})
    return pd.DataFrame(rows)

def main() -> None:
    RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = generate_ticket_data()
    df.to_csv(RAW_DATA_PATH, index=False)
    print(f"Generated {len(df)} support tickets at {RAW_DATA_PATH}")

if __name__ == "__main__":
    main()
