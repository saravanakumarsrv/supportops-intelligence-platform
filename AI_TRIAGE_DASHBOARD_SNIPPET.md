# AI Triage Agent Dashboard Snippet

## Step 1: Add this import near the top of `app/dashboard.py`

```python
from ai_agent.agent import analyze_ticket
```

## Step 2: Add this tab name to your `st.tabs([...])` list

```python
"AI Triage Agent",
```

Example:

```python
tabs = st.tabs(
    [
        "Executive Summary",
        "SLA & Resolution",
        "Sentiment & Risk",
        "Agent Performance",
        "Root Cause & Recommendations",
        "AI Triage Agent",
        "Raw Data",
    ]
)
```

## Step 3: Add this tab block before the Raw Data tab block

Important: adjust `tabs[5]` / `tabs[6]` based on your tab order.

```python
with tabs[5]:
    st.subheader("AI Ticket Triage Agent")

    st.info(
        "Teacher note: This agent reviews one ticket, checks risk signals, "
        "recommends an action, drafts a customer response, and shows its tool trace."
    )

    ticket_options = scored_df["ticket_id"].tolist()
    selected_ticket_id = st.selectbox("Select a ticket to analyze", ticket_options)

    selected_ticket = scored_df[scored_df["ticket_id"] == selected_ticket_id].iloc[0]

    if st.button("Analyze Ticket"):
        agent_result = analyze_ticket(selected_ticket)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Risk Score", f"{agent_result['risk_score']}/100")
        col2.metric("Risk Level", agent_result["risk_level"])
        col3.metric("SLA Status", agent_result["sla_status"])
        col4.metric("Urgency", agent_result["urgency"])

        st.subheader("Recommended Action")
        st.write(f"**Action Level:** {agent_result['action_level']}")
        st.write(f"**Recommended Action:** {agent_result['recommended_action']}")
        st.write(f"**Routing Recommendation:** {agent_result['routing_recommendation']}")
        st.write(f"**Business Impact:** {agent_result['business_impact']}")
        st.write(f"**Why this matters:** {agent_result['business_reason']}")

        st.subheader("Why This Ticket Is Risky")
        for factor in agent_result["risk_factors"]:
            st.write(f"- {factor}")

        st.subheader("Internal Manager Note")
        st.write(agent_result["internal_manager_note"])

        st.subheader("Customer Response Draft")
        st.write(agent_result["customer_response_draft"])

        st.subheader("Agent Trace")
        for step in agent_result["agent_trace"]:
            st.write(f"✅ {step}")
```

## Step 4: If you added AI Triage before Raw Data

Your Raw Data tab index will move one number later.

For example, if Raw Data was:

```python
with tabs[5]:
```

Change it to:

```python
with tabs[6]:
```
