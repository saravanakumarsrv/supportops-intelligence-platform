"""
Data Validator for SupportOps AI Analyzer

Teacher note:
Real business data is messy. Before analysis, a good analytics app must check:
- Are required columns present?
- Are dates valid?
- Are ticket IDs duplicated?
- Are important fields missing?

This module makes the project feel like a real product, not just a dashboard.
"""

from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = [
    "ticket_id",
    "customer_id",
    "department",
    "issue_type",
    "priority",
    "agent",
    "channel",
    "created_at",
    "sla_due_at",
    "closed_at",
    "status",
    "previous_contacts",
    "customer_message",
    "customer_rating",
]

VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}
VALID_STATUSES = {"Open", "Closed", "Escalated"}


def validate_required_columns(df: pd.DataFrame) -> dict:
    """Check whether uploaded file contains required columns."""
    existing_columns = set(df.columns)
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in existing_columns]

    return {
        "passed": len(missing_columns) == 0,
        "missing_columns": missing_columns,
        "required_columns": REQUIRED_COLUMNS,
        "uploaded_columns": list(df.columns),
    }


def clean_support_ticket_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean uploaded support ticket data.

    This does not aggressively change user data.
    It standardizes obvious type issues so the analytics engine can run.
    """
    cleaned = df.copy()

    # Strip whitespace from column names
    cleaned.columns = [col.strip() for col in cleaned.columns]

    # Strip whitespace in text columns
    text_columns = [
        "ticket_id",
        "customer_id",
        "department",
        "issue_type",
        "priority",
        "agent",
        "channel",
        "status",
        "customer_message",
    ]

    for col in text_columns:
        if col in cleaned.columns:
            cleaned[col] = cleaned[col].astype(str).str.strip()

    # Convert numeric fields
    if "previous_contacts" in cleaned.columns:
        cleaned["previous_contacts"] = pd.to_numeric(
            cleaned["previous_contacts"], errors="coerce"
        ).fillna(0).astype(int)

    if "customer_rating" in cleaned.columns:
        cleaned["customer_rating"] = pd.to_numeric(
            cleaned["customer_rating"], errors="coerce"
        ).fillna(3).astype(int)

    return cleaned


def data_quality_report(df: pd.DataFrame) -> dict:
    """Create a data quality report for uploaded support ticket data."""
    report = {}

    total_rows = len(df)
    total_columns = len(df.columns)

    missing_values = df.isna().sum()
    missing_value_total = int(missing_values.sum())

    duplicate_ticket_count = 0
    if "ticket_id" in df.columns:
        duplicate_ticket_count = int(df["ticket_id"].duplicated().sum())

    invalid_priority_count = 0
    if "priority" in df.columns:
        invalid_priority_count = int((~df["priority"].isin(VALID_PRIORITIES)).sum())

    invalid_status_count = 0
    if "status" in df.columns:
        invalid_status_count = int((~df["status"].isin(VALID_STATUSES)).sum())

    invalid_date_count = 0
    for date_col in ["created_at", "sla_due_at", "closed_at"]:
        if date_col in df.columns:
            converted = pd.to_datetime(df[date_col], errors="coerce")
            # closed_at can be blank for open tickets, so don't punish blank closed_at too harshly.
            if date_col == "closed_at":
                invalid_date_count += int(converted.isna().sum() - df[date_col].isna().sum())
            else:
                invalid_date_count += int(converted.isna().sum())

    missing_message_count = 0
    if "customer_message" in df.columns:
        missing_message_count = int(
            df["customer_message"].isna().sum()
            + (df["customer_message"].astype(str).str.strip() == "").sum()
        )

    issues = []

    if duplicate_ticket_count > 0:
        issues.append(f"{duplicate_ticket_count} duplicate ticket IDs found")

    if invalid_priority_count > 0:
        issues.append(f"{invalid_priority_count} invalid priority values found")

    if invalid_status_count > 0:
        issues.append(f"{invalid_status_count} invalid status values found")

    if invalid_date_count > 0:
        issues.append(f"{invalid_date_count} invalid date values found")

    if missing_message_count > 0:
        issues.append(f"{missing_message_count} missing customer messages found")

    if missing_value_total > 0:
        issues.append(f"{missing_value_total} total missing values found")

    # Simple scoring model out of 100.
    penalty = 0
    penalty += min(duplicate_ticket_count * 2, 20)
    penalty += min(invalid_priority_count * 2, 15)
    penalty += min(invalid_status_count * 2, 15)
    penalty += min(invalid_date_count * 2, 20)
    penalty += min(missing_message_count, 15)
    penalty += min(missing_value_total // max(total_rows, 1), 15)

    quality_score = max(0, 100 - penalty)

    report["total_rows"] = total_rows
    report["total_columns"] = total_columns
    report["missing_value_total"] = missing_value_total
    report["duplicate_ticket_count"] = duplicate_ticket_count
    report["invalid_priority_count"] = invalid_priority_count
    report["invalid_status_count"] = invalid_status_count
    report["invalid_date_count"] = invalid_date_count
    report["missing_message_count"] = missing_message_count
    report["quality_score"] = quality_score
    report["issues"] = issues if issues else ["No major data quality issues found"]

    return report
