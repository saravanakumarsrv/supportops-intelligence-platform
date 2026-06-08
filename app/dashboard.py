"""
Lesson purpose:
This file is the user interface.

Why?
Code is useful, but decision-makers need a dashboard.
Streamlit lets us turn Python analysis into an interactive business product.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from kpi_engine import calculate_kpis, agent_performance_summary, issue_type_summary
from recommendation_engine import generate_recommendations
from risk_scoring import add_risk_score, top_high_risk_tickets
from root_cause_analyzer import top_pain_points
from sla_analyzer import sla_summary_by_department, sla_summary_by_priority

DATA_PATH = Path("data/raw/support_tickets.csv")
st.set_page_config(page_title="SupportOps Intelligence Platform", page_icon="🎧", layout="wide")

@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        st.error("Data file not found. Run this first: python app/data_generator.py")
        st.stop()
    return pd.read_csv(DATA_PATH)

df = load_data()
scored_df = add_risk_score(df)
st.title("SupportOps Intelligence Platform")
st.caption("Customer support analytics, SLA monitoring, sentiment analysis, escalation risk scoring, and business recommendations")
tabs = st.tabs(["Executive Summary", "SLA & Resolution", "Sentiment & Risk", "Agent Performance", "Root Cause & Recommendations", "Raw Data"])
with tabs[0]:
    st.subheader("Executive Summary")
    kpis = calculate_kpis(df)
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
    issue_summary = issue_type_summary(df)
    fig = px.bar(issue_summary, x="issue_type", y="total_tickets", title="Ticket Volume by Issue Type", text="total_tickets")
    st.plotly_chart(fig, use_container_width=True)
with tabs[1]:
    st.subheader("SLA & Resolution Analysis")
    dept_sla = sla_summary_by_department(df)
    fig = px.bar(dept_sla, x="department", y="sla_breach_rate", title="SLA Breach Rate by Department", text="sla_breach_rate")
    st.plotly_chart(fig, use_container_width=True)
    priority_sla = sla_summary_by_priority(df)
    fig = px.bar(priority_sla, x="priority", y="sla_breach_rate", title="SLA Breach Rate by Priority", text="sla_breach_rate")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(dept_sla, use_container_width=True)
with tabs[2]:
    st.subheader("Sentiment & Escalation Risk")
    sentiment_counts = scored_df["sentiment"].value_counts().reset_index()
    sentiment_counts.columns = ["sentiment", "count"]
    fig = px.pie(sentiment_counts, names="sentiment", values="count", title="Customer Sentiment Breakdown")
    st.plotly_chart(fig, use_container_width=True)
    risk_counts = scored_df["risk_level"].value_counts().reset_index()
    risk_counts.columns = ["risk_level", "count"]
    fig = px.bar(risk_counts, x="risk_level", y="count", title="Escalation Risk Levels", text="count")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Top High-Risk Tickets")
    st.dataframe(top_high_risk_tickets(df), use_container_width=True)
with tabs[3]:
    st.subheader("Agent Performance")
    agent_summary = agent_performance_summary(df)
    fig = px.bar(agent_summary, x="agent", y="total_tickets", title="Ticket Workload by Agent", text="total_tickets")
    st.plotly_chart(fig, use_container_width=True)
    fig = px.bar(agent_summary, x="agent", y="sla_breach_rate", title="SLA Breach Rate by Agent", text="sla_breach_rate")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(agent_summary, use_container_width=True)
with tabs[4]:
    st.subheader("Root Cause & Recommendations")
    pain_points = top_pain_points(df)
    st.write("Top department and issue combinations causing support risk:")
    st.dataframe(pain_points, use_container_width=True)
    st.subheader("Business Recommendations")
    recommendations = generate_recommendations(df)
    for idx, rec in enumerate(recommendations, start=1):
        with st.expander(f"{idx}. {rec['opportunity']}", expanded=True):
            st.write(f"**Reason:** {rec['reason']}")
            st.write(f"**Recommendation:** {rec['recommendation']}")
            st.write(f"**Expected Impact:** {rec['impact']}")
            st.write(f"**Implementation Difficulty:** {rec['difficulty']}")
with tabs[5]:
    st.subheader("Raw Ticket Data")
    st.dataframe(scored_df, use_container_width=True)
