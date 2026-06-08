"""
Agent Tools

Teacher note:
These functions are the tools the AI agent uses.

In agentic AI, the agent does not do everything in one block.
It uses small tools:
- inspect ticket
- find risk factors
- choose action
- draft response
- create trace

This makes the workflow explainable.
"""

from __future__ import annotations


def normalize_ticket(ticket) -> dict:
    """Convert a pandas row/Series into a normal Python dictionary."""
    if hasattr(ticket, "to_dict"):
        return ticket.to_dict()
    return dict(ticket)


def identify_risk_factors(ticket: dict) -> list[str]:
    """Explain why a ticket is risky in business-friendly language."""
    factors: list[str] = []

    priority = str(ticket.get("priority", ""))
    sla_status = str(ticket.get("sla_status", ""))
    sentiment = str(ticket.get("sentiment", ""))
    previous_contacts = int(ticket.get("previous_contacts", 0))
    customer_rating = int(ticket.get("customer_rating", 3))
    status = str(ticket.get("status", ""))
    risk_score = int(ticket.get("escalation_risk_score", 0))

    if priority in ["High", "Critical"]:
        factors.append(f"{priority} priority ticket")

    if sla_status == "Breached":
        factors.append("SLA is already breached")
    elif sla_status == "At Risk":
        factors.append("Ticket is close to SLA breach")

    if sentiment in ["Negative", "Very Negative"]:
        factors.append(f"Customer sentiment is {sentiment.lower()}")

    if previous_contacts >= 3:
        factors.append(f"Customer has contacted support {previous_contacts} times")

    if customer_rating <= 2:
        factors.append(f"Low customer rating: {customer_rating}/5")

    if status == "Escalated":
        factors.append("Ticket is already escalated")

    if risk_score >= 85:
        factors.append("Overall escalation risk score is very high")

    if not factors:
        factors.append("No major escalation indicators found")

    return factors


def generate_agent_trace(ticket: dict, action_plan: dict) -> list[str]:
    """Show the step-by-step agent workflow."""
    ticket_id = str(ticket.get("ticket_id", "Unknown Ticket"))

    return [
        f"Loaded ticket {ticket_id}",
        f"Checked SLA status: {ticket.get('sla_status', 'Unknown')}",
        f"Analyzed customer sentiment: {ticket.get('sentiment', 'Unknown')}",
        f"Reviewed previous contacts: {ticket.get('previous_contacts', 0)}",
        f"Calculated escalation risk score: {ticket.get('escalation_risk_score', 0)}/100",
        f"Selected action level: {action_plan.get('action_level', 'Unknown')}",
        "Drafted internal manager note",
        "Drafted customer response for human review",
    ]
