"""
Customer Response Generator

Teacher note:
This file creates response drafts, not automatic emails.

Why this matters:
In real support operations, AI should assist humans.
It should draft helpful language, but a support agent or manager should review before sending.
"""

from __future__ import annotations


def draft_customer_response(ticket: dict, action_plan: dict) -> str:
    """Create a customer-facing draft response based on ticket context."""
    issue_type = str(ticket.get("issue_type", "your issue"))
    sentiment = str(ticket.get("sentiment", "Neutral"))
    sla_status = str(ticket.get("sla_status", ""))
    action_level = str(action_plan.get("action_level", "Normal Queue"))

    if action_level in ["Critical Escalation", "Manager Review"]:
        return (
            "Hi [Customer Name], I’m sorry for the delay and the inconvenience this has caused. "
            f"I can see that your {issue_type.lower()} request needs urgent attention, so I’m escalating it for review now. "
            "We will provide an update as soon as possible and make sure this is handled with priority."
        )

    if sentiment in ["Negative", "Very Negative"]:
        return (
            "Hi [Customer Name], I’m sorry this experience has been frustrating. "
            f"We are reviewing your {issue_type.lower()} request and will follow up with an update shortly. "
            "Thank you for your patience while we work on this."
        )

    if sla_status == "At Risk":
        return (
            "Hi [Customer Name], thank you for reaching out. "
            f"We are actively reviewing your {issue_type.lower()} request and will provide an update before the next step in the process."
        )

    return (
        "Hi [Customer Name], thank you for contacting support. "
        f"We have received your {issue_type.lower()} request and our team will continue working on it through the standard support process."
    )


def create_internal_manager_note(ticket: dict, action_plan: dict, risk_factors: list[str]) -> str:
    """Create an internal note for support managers."""
    ticket_id = str(ticket.get("ticket_id", "Unknown Ticket"))
    department = str(ticket.get("department", "Support"))
    issue_type = str(ticket.get("issue_type", "Customer Issue"))
    risk_score = int(ticket.get("escalation_risk_score", 0))
    action_level = str(action_plan.get("action_level", "Normal Queue"))

    factor_text = "; ".join(risk_factors) if risk_factors else "No major risk factors detected."

    return (
        f"{ticket_id} should be reviewed as '{action_level}'. "
        f"The ticket belongs to {department} and issue type '{issue_type}'. "
        f"Current escalation risk score is {risk_score}/100. "
        f"Key risk factors: {factor_text}"
    )
