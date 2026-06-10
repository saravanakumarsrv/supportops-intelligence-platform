"""
AI Ticket Triage Agent

This file runs the SupportOps AI ticket triage workflow.

Upgrade:
- Uses Google Gemini when GEMINI_API_KEY is available
- Falls back to the original rule-based agent if Gemini is unavailable
- Keeps the same output fields expected by the Streamlit dashboard
"""

from __future__ import annotations

import json
import os
import re

from google import genai

from ai_agent.action_planner import classify_business_impact, recommend_action
from ai_agent.response_generator import create_internal_manager_note, draft_customer_response
from ai_agent.tools import generate_agent_trace, identify_risk_factors, normalize_ticket


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


def fallback_analyze_ticket(ticket) -> dict:
    """
    Original rule-based ticket triage agent.
    Used when Gemini is unavailable or returns invalid output.
    """
    ticket_data = normalize_ticket(ticket)

    risk_factors = identify_risk_factors(ticket_data)
    action_plan = recommend_action(ticket_data)
    business_impact = classify_business_impact(ticket_data)
    customer_response = draft_customer_response(ticket_data, action_plan)
    internal_note = create_internal_manager_note(ticket_data, action_plan, risk_factors)
    trace = generate_agent_trace(ticket_data, action_plan)

    trace.append("Fallback rule-based agent used.")

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


def extract_json(text: str) -> dict:
    """
    Extract JSON safely from Gemini response.
    Handles normal JSON and JSON inside ```json code blocks.
    """
    if not text:
        raise ValueError("Empty Gemini response")

    cleaned = text.strip()

    cleaned = re.sub(r"^```json", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"^```", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not json_match:
        raise ValueError("No JSON object found in Gemini response")

    return json.loads(json_match.group(0))


def build_ticket_prompt(ticket_data: dict, fallback_result: dict) -> str:
    """
    Build a structured prompt for Gemini.
    """
    return f"""
You are an expert AI support operations analyst.

Analyze this customer support ticket and return ONLY valid JSON.
Do not include markdown.
Do not include explanations outside JSON.

Your JSON must use this exact schema:

{{
  "risk_score": 0,
  "risk_level": "Low | Medium | High | Critical",
  "sla_status": "On Track | At Risk | Breached | Unknown",
  "sentiment": "Positive | Neutral | Negative | Frustrated | Angry",
  "action_level": "Monitor | Standard Action | Priority Action | Escalation Required",
  "recommended_action": "clear next action for the support team",
  "routing_recommendation": "which team or role should handle this ticket",
  "urgency": "Low | Medium | High | Critical",
  "business_reason": "brief reason for the recommendation",
  "business_impact": "brief business impact",
  "risk_factors": ["risk factor 1", "risk factor 2"],
  "internal_manager_note": "short manager-facing note",
  "customer_response_draft": "professional customer-facing response",
  "agent_trace": ["step 1", "step 2", "step 3"]
}}

Ticket data:
{json.dumps(ticket_data, indent=2, default=str)}

Rule-based baseline result:
{json.dumps(fallback_result, indent=2, default=str)}

Important rules:
- Keep risk_score as an integer from 0 to 100.
- Use the baseline result as guidance, but improve the reasoning and writing.
- If SLA is breached or customer sentiment is angry/frustrated, increase urgency.
- The customer response must be empathetic, professional, and specific.
- The manager note must be concise and action-oriented.
- Return only valid JSON.
"""


def analyze_ticket(ticket) -> dict:
    """
    Run AI ticket triage.

    Uses Gemini when GEMINI_API_KEY is available.
    Falls back to the rule-based agent if anything fails.
    """
    ticket_data = normalize_ticket(ticket)
    fallback_result = fallback_analyze_ticket(ticket)

    if not os.getenv("GEMINI_API_KEY"):
        fallback_result["agent_trace"].append("GEMINI_API_KEY not found. Used fallback mode.")
        return fallback_result

    try:
        client = genai.Client()
        prompt = build_ticket_prompt(ticket_data, fallback_result)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        llm_result = extract_json(response.text)

        final_result = {
            "ticket_id": ticket_data.get("ticket_id"),
            "risk_score": int(llm_result.get("risk_score", fallback_result["risk_score"])),
            "risk_level": llm_result.get("risk_level", fallback_result["risk_level"]),
            "sla_status": llm_result.get("sla_status", fallback_result["sla_status"]),
            "sentiment": llm_result.get("sentiment", fallback_result["sentiment"]),
            "action_level": llm_result.get("action_level", fallback_result["action_level"]),
            "recommended_action": llm_result.get("recommended_action", fallback_result["recommended_action"]),
            "routing_recommendation": llm_result.get(
                "routing_recommendation",
                fallback_result["routing_recommendation"],
            ),
            "urgency": llm_result.get("urgency", fallback_result["urgency"]),
            "business_reason": llm_result.get("business_reason", fallback_result["business_reason"]),
            "business_impact": llm_result.get("business_impact", fallback_result["business_impact"]),
            "risk_factors": llm_result.get("risk_factors", fallback_result["risk_factors"]),
            "internal_manager_note": llm_result.get(
                "internal_manager_note",
                fallback_result["internal_manager_note"],
            ),
            "customer_response_draft": llm_result.get(
                "customer_response_draft",
                fallback_result["customer_response_draft"],
            ),
            "agent_trace": llm_result.get("agent_trace", fallback_result["agent_trace"]),
        }

        final_result["agent_trace"].append(f"Gemini LLM analysis completed using {GEMINI_MODEL}.")
        return final_result

    except Exception as error:
        fallback_result["agent_trace"].append(f"Gemini failed. Fallback used. Error: {error}")
        return fallback_result