# Upload-Based AI Analyzer Design

## Product Flow

The app works as an upload-based AI analytics product:

1. User uploads support ticket CSV
2. App validates required columns
3. App checks data quality
4. App cleans basic field types
5. App runs SLA analysis
6. App runs sentiment analysis
7. App calculates escalation risk
8. App generates AI triage recommendations
9. App generates daily manager briefing
10. User downloads manager report

## Why This Is Strong

This is stronger than a static dashboard because the user can bring their own data. It behaves like a real analytics tool.

## Required Columns

- ticket_id
- customer_id
- department
- issue_type
- priority
- agent
- channel
- created_at
- sla_due_at
- closed_at
- status
- previous_contacts
- customer_message
- customer_rating

## Business Value

The app helps support managers quickly understand SLA risk, customer frustration, escalation risk, overloaded agents, and root-cause issues.
