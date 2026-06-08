"""
Action Planner

Teacher note:
This file decides what the business should do next.

Why this matters:
Analytics tells us what is happening.
An action planner tells the team what to do about it.
That is the difference between a dashboard and a decision-support system.
"""

from __future__ import annotations


def recommend_action(ticket: dict) -> dict:
    """
    Recommend a support action based on ticket risk.

    This is rule-based agent logic.
    Later, this can be replaced or enhanced with an LLM.
    """
    risk_score = int(ticket.get("escalation_risk_score", 0))
    sla_status = str(ticket.get("sla_status", ""))
    sentiment = str(ticket.get("sentiment", ""))
    priority = str(ticket.get("priority", ""))
    department = str(ticket.get("department", "Support"))
    issue_type = str(ticket.get("issue_type", "Customer Issue"))

    if risk_score >= 85 or (
        sla_status == "Breached"
        and sentiment in ["Negative", "Very Negative"]
        and priority in ["High", "Critical"]
    ):
        return {
            "action_level": "Critical Escalation",
            "recommended_action": f"Escalate immediately to a senior {department} specialist.",
            "routing_recommendation": f"Route to senior {department} queue with priority handling.",
            "urgency": "Immediate",
            "business_reason": (
                "This ticket has strong escalation signals and should be handled before normal queue items."
            ),
        }

    if risk_score >= 70:
        return {
            "action_level": "Manager Review",
            "recommended_action": f"Send to {department} manager review and prioritize for same-day update.",
            "routing_recommendation": f"Route to experienced {department} agent.",
            "urgency": "High",
            "business_reason": (
                "The customer may escalate if the issue is not handled quickly."
            ),
        }

    if risk_score >= 50:
        return {
            "action_level": "Monitor Closely",
            "recommended_action": "Keep in active queue and provide proactive customer update.",
            "routing_recommendation": f"Keep with assigned agent unless SLA risk increases.",
            "urgency": "Medium",
            "business_reason": (
                "The ticket has moderate risk and should not be allowed to age without communication."
            ),
        }

    return {
        "action_level": "Normal Queue",
        "recommended_action": "Handle through standard support workflow.",
        "routing_recommendation": "No special routing required.",
        "urgency": "Normal",
        "business_reason": (
            "The ticket does not currently show strong escalation indicators."
        ),
    }


def classify_business_impact(ticket: dict) -> str:
    """Classify likely business impact from ticket conditions."""
    risk_score = int(ticket.get("escalation_risk_score", 0))
    rating = int(ticket.get("customer_rating", 3))
    sentiment = str(ticket.get("sentiment", ""))
    status = str(ticket.get("status", ""))

    if risk_score >= 85 or (rating <= 2 and sentiment in ["Negative", "Very Negative"]):
        return "High customer churn or complaint risk"
    if status == "Escalated" or risk_score >= 70:
        return "High support escalation risk"
    if risk_score >= 50:
        return "Moderate customer experience risk"
    return "Low immediate business risk"
