"""
SupportOps AI Analyzer

Product flow:
Home -> Upload CSV -> Validate data -> Run analytics -> Run AI agents -> Download manager report.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from ai_agent.agent import analyze_ticket
from ai_agent.briefing_agent import generate_daily_briefing, generate_briefing_text
from data_validator import (
    REQUIRED_COLUMNS,
    clean_support_ticket_data,
    data_quality_report,
    validate_required_columns,
)
from kpi_engine import calculate_kpis, agent_performance_summary, issue_type_summary
from recommendation_engine import generate_recommendations
from risk_scoring import add_risk_score, top_high_risk_tickets
from root_cause_analyzer import top_pain_points
from sla_analyzer import sla_summary_by_department, sla_summary_by_priority


DATA_PATH = Path("data/raw/support_tickets.csv")

st.set_page_config(
    page_title="SupportOps AI Analyzer",
    page_icon="🎧",
    layout="wide",
)


def add_custom_css() -> None:
    """Add simple product-style UI styling."""
    st.markdown(
        """
        <style>
        .hero-container {
            padding: 2rem 2rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #111827 0%, #1f2937 45%, #0f172a 100%);
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 1.5rem;
        }
        .hero-title {
            font-size: 3rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.05;
            margin-bottom: 0.75rem;
        }
        .hero-subtitle {
            font-size: 1.1rem;
            color: #cbd5e1;
            max-width: 900px;
        }
        .section-card {
            padding: 1.2rem;
            border-radius: 14px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            height: 100%;
        }
        .metric-card {
            padding: 1.3rem;
            border-radius: 16px;
            background: rgba(59,130,246,0.10);
            border: 1px solid rgba(59,130,246,0.25);
            height: 100%;
        }
        .metric-number {
            font-size: 2.2rem;
            font-weight: 800;
            color: #93c5fd;
            margin-bottom: 0.3rem;
        }
        .metric-label {
            color: #e5e7eb;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .metric-source {
            color: #9ca3af;
            font-size: 0.85rem;
        }
        .workflow-step {
            padding: 0.9rem 1rem;
            border-left: 4px solid #3b82f6;
            background: rgba(255,255,255,0.035);
            border-radius: 10px;
            margin-bottom: 0.65rem;
        }
        .small-muted {
            color: #9ca3af;
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_default_data() -> pd.DataFrame:
    """Load default generated support ticket dataset."""
    if not DATA_PATH.exists():
        st.error("Data file not found. Run this first: python app/data_generator.py")
        st.stop()

    return pd.read_csv(DATA_PATH)


def apply_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Apply dashboard filters selected by the user."""
    st.sidebar.header("Dashboard Filters")

    filtered = df.copy()

    filter_columns = [
        ("department", "Department"),
        ("priority", "Priority"),
        ("agent", "Agent"),
        ("issue_type", "Issue Type"),
        ("status", "Status"),
        ("channel", "Channel"),
    ]

    for column, label in filter_columns:
        if column in filtered.columns:
            values = sorted(filtered[column].dropna().unique().tolist())
            selected = st.sidebar.multiselect(label, values, default=values)
            filtered = filtered[filtered[column].isin(selected)]

    return filtered


def render_home_page() -> None:
    """Render product landing page."""
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">SupportOps AI Analyzer</div>
            <div class="hero-subtitle">
                Upload customer support ticket data and let an AI operations workflow identify SLA risks,
                customer frustration, escalation risk, overloaded agents, root-cause patterns, and manager-ready actions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Why this matters")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-number">32%</div>
                <div class="metric-label">of customers may leave after one bad experience</div>
                <div class="metric-source">Source: PwC Future of Customer Experience</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-number">&gt;50%</div>
                <div class="metric-label">may switch after one unsatisfactory customer experience</div>
                <div class="metric-source">Source: Zendesk CX statistics</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-number">$3T</div>
                <div class="metric-label">in global sales could be at risk from poor customer experiences</div>
                <div class="metric-source">Source: Qualtrics XM Institute</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.subheader("What the app does")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="section-card">
                <h4>1. Upload & Validate</h4>
                <p>Upload support ticket CSV data. The app checks required columns, missing values, duplicate ticket IDs, invalid dates, and data quality score.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="section-card">
                <h4>2. Analyze Operations</h4>
                <p>Generate KPIs for SLA breaches, resolution time, sentiment, escalation risk, customer ratings, agent workload, and root-cause issues.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="section-card">
                <h4>3. AI Action Briefing</h4>
                <p>Use an AI triage agent and daily briefing agent to recommend actions, draft customer responses, and create manager-ready reports.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    left, right = st.columns([1, 1])

    with left:
        st.subheader("AI workflow")
        st.markdown(
            """
            <div class="workflow-step"><b>Step 1:</b> Upload support ticket data</div>
            <div class="workflow-step"><b>Step 2:</b> Validate data quality and required fields</div>
            <div class="workflow-step"><b>Step 3:</b> Run SLA, sentiment, and risk analysis</div>
            <div class="workflow-step"><b>Step 4:</b> Triage high-risk tickets with the AI agent</div>
            <div class="workflow-step"><b>Step 5:</b> Generate a daily manager briefing and downloadable report</div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.subheader("Built for")
        st.write("- Customer Support Managers")
        st.write("- Operations Analysts")
        st.write("- Business Analysts")
        st.write("- Customer Experience Teams")
        st.write("- Support QA / Workforce Teams")

        st.info(
            "Start in the sidebar: upload your CSV file, or check 'Use demo sample data' to explore the app."
        )

    st.caption(
        "Portfolio note: This app uses rule-based agentic workflows by default so it can run without paid API keys."
    )


def render_upload_guidance() -> None:
    """Render upload instructions when no data is selected."""
    st.subheader("Upload support ticket data to begin")

    st.write(
        "Use the sidebar to upload a CSV file. If you only want to test the product, select "
        "**Use demo sample data** in the sidebar."
    )

    st.subheader("Required CSV Columns")
    st.code(", ".join(REQUIRED_COLUMNS))

    st.subheader("Expected data examples")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "ticket_id": "TKT-00001",
                    "customer_id": "CUST-1010",
                    "department": "Billing",
                    "issue_type": "Refund Delay",
                    "priority": "High",
                    "agent": "Ava",
                    "channel": "Email",
                    "created_at": "2025-06-01 09:00:00",
                    "sla_due_at": "2025-06-02 09:00:00",
                    "closed_at": "2025-06-03 14:30:00",
                    "status": "Escalated",
                    "previous_contacts": 3,
                    "customer_message": "I have contacted support multiple times and nobody has helped me.",
                    "customer_rating": 1,
                }
            ]
        ),
        use_container_width=True,
    )


add_custom_css()

st.sidebar.header("Upload Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload support ticket CSV",
    type=["csv"],
    help="Upload a CSV with support ticket fields.",
)

use_demo_data = st.sidebar.checkbox("Use demo sample data")

tabs = st.tabs(
    [
        "Home",
        "Upload & Validate Data",
        "Executive Summary",
        "SLA & Resolution",
        "Sentiment & Risk",
        "Agent Performance",
        "Root Cause Analysis",
        "AI Ticket Triage Agent",
        "Daily AI Briefing",
        "Download Report",
        "Raw Data",
    ]
)

with tabs[0]:
    render_home_page()

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)
    data_source = f"Uploaded file: {uploaded_file.name}"
elif use_demo_data:
    raw_df = load_default_data()
    data_source = "Demo sample dataset"
else:
    with tabs[1]:
        render_upload_guidance()
    st.stop()

raw_df = clean_support_ticket_data(raw_df)
column_check = validate_required_columns(raw_df)

with tabs[1]:
    st.subheader("Upload & Validate Data")

    st.info(
        "Teacher note: Before analytics, we validate the uploaded file. "
        "Real business data is often messy, so data quality checks are part of professional analytics work."
    )

    col1, col2, col3 = st.columns(3)
    col1.write("**Data Source**")
    col1.write(data_source)
    col2.metric("Rows Detected", f"{len(raw_df):,}")
    col3.metric("Columns Detected", f"{len(raw_df.columns):,}")

    if column_check["passed"]:
        st.success("Required column check passed. The dataset is ready for analysis.")
    else:
        st.error("Required column check failed. Some required columns are missing.")
        st.write("Missing columns:")
        for col in column_check["missing_columns"]:
            st.write(f"- {col}")

        st.write("Required columns:")
        st.code(", ".join(REQUIRED_COLUMNS))

    quality = data_quality_report(raw_df)

    st.subheader("Data Quality Report")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Data Quality Score", f"{quality['quality_score']}/100")
    col2.metric("Missing Values", quality["missing_value_total"])
    col3.metric("Duplicate Ticket IDs", quality["duplicate_ticket_count"])
    col4.metric("Invalid Dates", quality["invalid_date_count"])

    col5, col6, col7 = st.columns(3)
    col5.metric("Invalid Priorities", quality["invalid_priority_count"])
    col6.metric("Invalid Statuses", quality["invalid_status_count"])
    col7.metric("Missing Messages", quality["missing_message_count"])

    st.subheader("Data Quality Issues")
    for issue in quality["issues"]:
        st.write(f"- {issue}")

    st.subheader("Uploaded Columns")
    st.write(list(raw_df.columns))

if not column_check["passed"]:
    st.warning("Fix missing columns before viewing analysis tabs.")
    st.stop()

filtered_df = apply_sidebar_filters(raw_df)

if filtered_df.empty:
    st.warning("No tickets match the selected filters. Adjust the sidebar filters.")
    st.stop()

scored_df = add_risk_score(filtered_df)

st.sidebar.markdown("---")
st.sidebar.metric("Filtered Tickets", f"{len(filtered_df):,}")
st.sidebar.metric("Total Tickets", f"{len(raw_df):,}")

with tabs[2]:
    st.subheader("Executive Summary")

    kpis = calculate_kpis(filtered_df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tickets", f"{kpis['total_tickets']:,}")
    col2.metric("Open Tickets", f"{kpis['open_tickets']:,}")
    col3.metric("SLA Breach Rate", f"{kpis['sla_breach_rate']}%")
    col4.metric("Avg Resolution Time", f"{kpis['avg_resolution_hours']} hrs")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Escalated Tickets", f"{kpis['escalated_tickets']:,}")
    col6.metric("Avg Customer Rating", f"{kpis['avg_customer_rating']}/5")
    col7.metric("High-Risk Tickets", f"{kpis['high_risk_tickets']:,}")
    col8.metric("Negative Sentiment", f"{kpis['negative_sentiment_rate']}%")

    issue_summary = issue_type_summary(filtered_df)
    fig = px.bar(
        issue_summary,
        x="issue_type",
        y="total_tickets",
        title="Ticket Volume by Issue Type",
        text="total_tickets",
    )
    st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.subheader("SLA & Resolution Analysis")

    dept_sla = sla_summary_by_department(filtered_df)
    fig = px.bar(
        dept_sla,
        x="department",
        y="sla_breach_rate",
        title="SLA Breach Rate by Department",
        text="sla_breach_rate",
    )
    st.plotly_chart(fig, use_container_width=True)

    priority_sla = sla_summary_by_priority(filtered_df)
    fig = px.bar(
        priority_sla,
        x="priority",
        y="sla_breach_rate",
        title="SLA Breach Rate by Priority",
        text="sla_breach_rate",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(dept_sla, use_container_width=True)

with tabs[4]:
    st.subheader("Sentiment & Escalation Risk")

    sentiment_counts = scored_df["sentiment"].value_counts().reset_index()
    sentiment_counts.columns = ["sentiment", "count"]

    fig = px.pie(
        sentiment_counts,
        names="sentiment",
        values="count",
        title="Customer Sentiment Breakdown",
    )
    st.plotly_chart(fig, use_container_width=True)

    risk_counts = scored_df["risk_level"].value_counts().reset_index()
    risk_counts.columns = ["risk_level", "count"]

    fig = px.bar(
        risk_counts,
        x="risk_level",
        y="count",
        title="Escalation Risk Levels",
        text="count",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top High-Risk Tickets")
    st.dataframe(top_high_risk_tickets(filtered_df), use_container_width=True)

with tabs[5]:
    st.subheader("Agent Performance")

    agent_summary = agent_performance_summary(filtered_df)

    fig = px.bar(
        agent_summary,
        x="agent",
        y="total_tickets",
        title="Ticket Workload by Agent",
        text="total_tickets",
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(
        agent_summary,
        x="agent",
        y="sla_breach_rate",
        title="SLA Breach Rate by Agent",
        text="sla_breach_rate",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(agent_summary, use_container_width=True)

with tabs[6]:
    st.subheader("Root Cause Analysis")

    pain_points = top_pain_points(filtered_df)
    st.write("Top department and issue combinations causing support risk:")
    st.dataframe(pain_points, use_container_width=True)

    st.subheader("Business Recommendations")
    recommendations = generate_recommendations(filtered_df)

    for idx, rec in enumerate(recommendations, start=1):
        with st.expander(f"{idx}. {rec['opportunity']}", expanded=True):
            st.write(f"**Reason:** {rec['reason']}")
            st.write(f"**Recommendation:** {rec['recommendation']}")
            st.write(f"**Expected Impact:** {rec['impact']}")
            st.write(f"**Implementation Difficulty:** {rec['difficulty']}")

with tabs[7]:
    st.subheader("AI Ticket Triage Agent")

    st.info(
        "Teacher note: This agent reviews one ticket, checks SLA, sentiment, risk score, "
        "previous contacts, and customer rating. Then it recommends action, drafts a customer response, "
        "and shows the agent trace."
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

with tabs[8]:
    st.subheader("Daily SupportOps AI Briefing")

    st.info(
        "Teacher note: The triage agent analyzes one ticket. "
        "This briefing agent analyzes the full support queue and creates a manager-ready action summary."
    )

    briefing = generate_daily_briefing(scored_df)

    st.subheader("Manager Summary")
    st.write(briefing["briefing_sections"]["executive_summary"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### SLA Risk")
        st.write(briefing["briefing_sections"]["sla_risk"])

        st.markdown("### Customer Sentiment Risk")
        st.write(briefing["briefing_sections"]["customer_sentiment_risk"])

    with col2:
        st.markdown("### Top Issue Risk")
        st.write(briefing["briefing_sections"]["top_issue_risk"])

        st.markdown("### Workload Risk")
        st.write(briefing["briefing_sections"]["workload_risk"])

    st.subheader("Recommended Actions")
    for idx, action in enumerate(briefing["recommended_actions"], start=1):
        st.write(f"{idx}. {action}")

    st.subheader("Top High-Risk Tickets")
    st.dataframe(briefing["top_high_risk_tickets"], use_container_width=True)

    st.subheader("Overloaded Agents")
    st.dataframe(briefing["overloaded_agents"], use_container_width=True)

    st.subheader("Top Root-Cause Pain Points")
    st.dataframe(briefing["top_pain_points"], use_container_width=True)

    st.subheader("Agent Trace")
    for step in briefing["agent_trace"]:
        st.write(f"✅ {step}")

with tabs[9]:
    st.subheader("Download Manager Report")

    st.info(
        "Teacher note: A real analytics app should not only show charts. "
        "It should help users export findings for managers or stakeholders."
    )

    report_text = generate_briefing_text(scored_df)

    st.text_area("Manager briefing report preview", report_text, height=360)

    st.download_button(
        label="Download Manager Briefing Report",
        data=report_text,
        file_name="supportops_manager_briefing.txt",
        mime="text/plain",
    )

with tabs[10]:
    st.subheader("Raw Ticket Data")
    st.dataframe(scored_df, use_container_width=True)
