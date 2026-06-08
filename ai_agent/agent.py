"""
AI Ticket Triage Agent

Teacher note:
This is the main agent brain.

Why it is agentic:
The agent receives a goal:
"Analyze this ticket and decide what should happen next."

Then it uses tools:
1. Normalize ticket
2. Identify risk factors
3. Plan action
4. Classify business impact
5. Draft customer response
6. Draft manager note
7. Return trace of steps

This is a rule-based agentic workflow.
It does not require an API key, so it is safe for GitHub and easy for recruiters to run.
"""

from __future__ import annotations

from ai_agent.action_planner import classify_business_impact, recommend_action
from ai_agent.response_generator import create_internal_manager_note, draft_customer_response
from ai_agent.tools import generate_agent_trace, identify_risk_factors, normalize_ticket


def analyze_ticket(ticket) -> dict:
    """
    Run the AI Ticket Triage Agent on one ticket.

    Returns a dictionary that can be displayed in Streamlit.
    """
    ticket_data = normalize_ticket(ticket)

    risk_factors = identify_risk_factors(ticket_data)
    action_plan = recommend_action(ticket_data)
    business_impact = classify_business_impact(ticket_data)
    customer_response = draft_customer_response(ticket_data, action_plan)
    internal_note = create_internal_manager_note(ticket_data, action_plan, risk_factors)
    trace = generate_agent_trace(ticket_data, action_plan)

    return {
        "ticket_id": ticket_data.get("ticket_id"),
        "risk_score": int(ticket_data.get("escalation_risk_score", 0)),
        "risk_level": ticket_data.get("risk_level", "Unknown"),
        "sla_status": ticket_data.get("sla_status", "Unknown"),
        "sentiment": ticket_data.get("sentiment", "Unknown"),
        "action_level": action_plan["action_level"],
        "recommended_action": action_plan["recommended_action"],
        "routing_recommendation": action_plan["routing_recommendation"],
        "urgency": action_plan["urgency"],
        "business_reason": action_plan["business_reason"],
        "business_impact": business_impact,
        "risk_factors": risk_factors,
        "internal_manager_note": internal_note,
        "customer_response_draft": customer_response,
        "agent_trace": trace,
    }
