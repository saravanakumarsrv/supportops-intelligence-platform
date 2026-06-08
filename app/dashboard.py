"""
OpsIntel AI - Professional Single-File Streamlit Dashboard

This file contains:
- Clean SaaS-style homepage
- Why Us page with ROI calculator
- SupportOps Analyzer connected to existing project logic
- CostOps Analyzer working demo
- NextHire AI working demo
- Professional light theme CSS embedded in this file

No external CSS folder required.
Replace your existing app/dashboard.py with this file.
"""

from __future__ import annotations

from pathlib import Path
import re
from collections import Counter

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
from risk_scoring import add_risk_score, top_high_risk_tickets
from sla_analyzer import sla_summary_by_department


DATA_PATH = Path("data/raw/support_tickets.csv")


st.set_page_config(
    page_title="OpsIntel AI",
    page_icon="◆",
    layout="wide",
)


# =============================================================================
# SESSION STATE
# =============================================================================
DEFAULT_STATE = {
    "page": "Home",
    "support_demo_enabled": False,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


def go_to(page_name: str) -> None:
    """Navigate to a main app page."""
    st.session_state["page"] = page_name
    st.rerun()


def enable_support_demo() -> None:
    """Enable demo support data and stay inside SupportOps."""
    st.session_state["support_demo_enabled"] = True
    st.session_state["page"] = "SupportOps Analyzer"
    st.rerun()


# =============================================================================
# EMBEDDED PROFESSIONAL CSS
# =============================================================================
def load_css() -> None:
    """Load professional SaaS-style CSS directly from this dashboard file."""
    st.markdown(
        """
        <style>
        :root {
            --color-primary: #3d3a8c;
            --color-primary-hover: #35327a;
            --color-primary-active: #2f2c6d;
            --color-primary-subtle: rgba(61, 58, 140, 0.08);
            --color-accent: #8faf9b;
            --color-accent-subtle: rgba(143, 175, 155, 0.16);

            --color-bg: #fafaf9;
            --color-bg-soft: #f9f8f6;
            --color-surface: #ffffff;
            --color-surface-subtle: #f4f3f0;
            --color-surface-hover: #fbfbfa;

            --color-border: #e8e7e3;
            --color-border-hover: #d7d5cf;

            --color-text-primary: #1c1c1a;
            --color-text-secondary: #6b6a66;
            --color-text-tertiary: #8b8983;
            --color-text-inverse: #ffffff;

            --color-success: #557c5f;
            --color-success-bg: #eff5f1;
            --color-warning: #9a7435;
            --color-warning-bg: #fbf4e8;
            --color-danger: #9b4a4a;
            --color-danger-bg: #fbeeee;

            --font-sans: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;

            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 22px;
            --radius-full: 999px;

            --shadow-xs: 0 1px 2px rgba(28, 28, 26, 0.04);
            --shadow-sm: 0 8px 20px rgba(28, 28, 26, 0.06);
            --shadow-md: 0 16px 40px rgba(28, 28, 26, 0.08);
            --shadow-lg: 0 24px 60px rgba(28, 28, 26, 0.10);

            --transition-fast: 120ms ease;
            --transition-medium: 180ms ease;
        }

        header,
        #MainMenu,
        footer {
            visibility: hidden;
        }

        html,
        body,
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at top left, rgba(61, 58, 140, 0.08), transparent 30%),
                radial-gradient(circle at top right, rgba(143, 175, 155, 0.10), transparent 28%),
                linear-gradient(180deg, #ffffff 0%, #fafaf9 42%, #f3f1ec 100%);
            color: var(--color-text-primary);
            font-family: var(--font-sans);
        }

        .block-container {
            max-width: 1220px;
            padding-top: 0.75rem;
            padding-bottom: 1rem;
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--color-border);
        }

        @keyframes fadeUp {
            from {
                opacity: 0;
                transform: translateY(16px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes softFloat {
            0% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-7px);
            }
            100% {
                transform: translateY(0);
            }
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.9rem 0 1rem 0;
            border-bottom: 1px solid var(--color-border);
            margin-bottom: 1.15rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .brand-logo {
            width: 46px;
            height: 46px;
            border-radius: 15px;
            background:
                radial-gradient(circle at 32% 22%, rgba(255,255,255,0.70), transparent 22%),
                linear-gradient(135deg, #3d3a8c 0%, #6f6baa 52%, #8faf9b 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 1.02rem;
            letter-spacing: -0.08em;
            box-shadow: 0 14px 30px rgba(61, 58, 140, 0.20);
            animation: softFloat 6s ease-in-out infinite;
        }

        .brand-name {
            font-size: 1.55rem;
            font-weight: 650;
            color: var(--color-text-primary);
            letter-spacing: -0.04em;
            line-height: 1;
        }

        .brand-name span {
            color: var(--color-primary);
        }

        .brand-subtitle {
            color: var(--color-text-secondary);
            font-size: 0.78rem;
            margin-top: 0.15rem;
        }

        .nav-note {
            padding: 0.4rem 0.78rem;
            border-radius: var(--radius-full);
            color: var(--color-primary);
            background: var(--color-primary-subtle);
            border: 1px solid rgba(61, 58, 140, 0.14);
            font-size: 0.82rem;
            font-weight: 600;
        }

        div.stButton > button {
            border-radius: var(--radius-sm);
            border: 1px solid var(--color-border);
            background: #ffffff;
            color: var(--color-text-primary);
            font-weight: 500;
            min-height: 2.55rem;
            box-shadow: none;
            transition:
                background-color var(--transition-fast),
                border-color var(--transition-fast),
                color var(--transition-fast),
                transform var(--transition-fast);
        }

        div.stButton > button:hover {
            border-color: var(--color-primary);
            background: var(--color-primary-subtle);
            color: var(--color-primary);
            transform: translateY(-1px);
        }

        div.stButton > button:active {
            transform: scale(0.985);
        }

        .hero {
            position: relative;
            padding: 3.2rem 2.7rem;
            border-radius: 28px;
            background:
                radial-gradient(circle at 85% 15%, rgba(61, 58, 140, 0.10), transparent 32%),
                radial-gradient(circle at 12% 88%, rgba(143, 175, 155, 0.12), transparent 32%),
                linear-gradient(135deg, #ffffff 0%, #fafaf9 52%, #f3f1ec 100%);
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-md);
            overflow: hidden;
            animation: fadeUp 0.65s ease-out;
        }

        .hero::after {
            content: "";
            position: absolute;
            width: 270px;
            height: 270px;
            border-radius: 50%;
            right: -90px;
            top: -90px;
            background: radial-gradient(circle, rgba(61,58,140,0.10), transparent 68%);
            animation: softFloat 8s ease-in-out infinite;
        }

        .eyebrow {
            display: inline-block;
            padding: 0.38rem 0.82rem;
            border-radius: var(--radius-full);
            color: var(--color-primary);
            background: var(--color-primary-subtle);
            border: 1px solid rgba(61, 58, 140, 0.14);
            font-weight: 600;
            font-size: 0.86rem;
            margin-bottom: 1rem;
        }

        .hero-title {
            color: var(--color-text-primary);
            font-size: clamp(2.4rem, 5vw, 4.6rem);
            line-height: 1.02;
            font-weight: 650;
            letter-spacing: -0.05em;
            max-width: 1000px;
            margin-bottom: 1rem;
        }

        .hero-title span {
            background: linear-gradient(90deg, #3d3a8c, #6f6baa, #557c5f);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-copy {
            color: var(--color-text-secondary);
            font-size: 1.08rem;
            line-height: 1.75;
            max-width: 860px;
            margin-bottom: 1.1rem;
        }

        .mini-proof-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            margin-top: 1.1rem;
        }

        .proof-pill {
            padding: 0.5rem 0.75rem;
            border-radius: var(--radius-full);
            background: #ffffff;
            border: 1px solid var(--color-border);
            color: var(--color-text-secondary);
            font-size: 0.86rem;
            font-weight: 500;
            box-shadow: var(--shadow-xs);
        }

        .section-title {
            margin-top: 2rem;
            margin-bottom: 0.85rem;
            color: var(--color-text-primary);
            font-size: 1.62rem;
            font-weight: 650;
            letter-spacing: -0.02em;
        }

        .section-copy {
            color: var(--color-text-secondary);
            margin-top: -0.4rem;
            margin-bottom: 1rem;
            line-height: 1.65;
        }

        .app-card {
            padding: 1.35rem;
            border-radius: var(--radius-md);
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
            min-height: 320px;
            animation: fadeUp 0.8s ease-out;
            transition:
                transform var(--transition-medium),
                border-color var(--transition-medium),
                box-shadow var(--transition-medium),
                background-color var(--transition-medium);
        }

        .app-card:hover {
            transform: translateY(-4px);
            border-color: var(--color-border-hover);
            box-shadow: var(--shadow-md);
            background: var(--color-surface-hover);
        }

        .icon-box {
            width: 52px;
            height: 52px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.45rem;
            margin-bottom: 0.95rem;
            background: var(--color-primary-subtle);
            color: var(--color-primary);
            border: 1px solid rgba(61, 58, 140, 0.12);
        }

        .icon-box.sage {
            background: var(--color-accent-subtle);
            color: var(--color-success);
            border-color: rgba(143, 175, 155, 0.24);
        }

        .icon-box.amber {
            background: var(--color-warning-bg);
            color: var(--color-warning);
            border-color: rgba(154, 116, 53, 0.18);
        }

        .app-title {
            color: var(--color-text-primary);
            font-size: 1.28rem;
            font-weight: 650;
            margin-bottom: 0.45rem;
        }

        .app-copy {
            color: var(--color-text-secondary);
            line-height: 1.6;
            min-height: 100px;
            font-size: 0.95rem;
        }

        .value-list {
            color: var(--color-primary);
            font-size: 0.88rem;
            margin-top: 0.7rem;
            line-height: 1.65;
            font-weight: 500;
        }

        .module-header {
            padding: 1.55rem;
            border-radius: var(--radius-lg);
            background:
                radial-gradient(circle at 82% 10%, rgba(61,58,140,0.08), transparent 34%),
                linear-gradient(135deg, #ffffff, #fafaf9);
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
            margin-bottom: 1.1rem;
            animation: fadeUp 0.65s ease-out;
        }

        .module-kicker {
            color: var(--color-primary);
            font-size: 0.82rem;
            font-weight: 600;
            margin-bottom: 0.35rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .module-title {
            color: var(--color-text-primary);
            font-size: 2.1rem;
            font-weight: 650;
            letter-spacing: -0.03em;
            margin-bottom: 0.3rem;
        }

        .module-copy {
            color: var(--color-text-secondary);
            line-height: 1.6;
        }

        .metric-card {
            padding: 1.2rem;
            border-radius: var(--radius-md);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
            height: 100%;
            animation: fadeUp 0.85s ease-out;
        }

        .metric-number {
            font-size: 2rem;
            font-weight: 650;
            color: var(--color-primary);
            margin-bottom: 0.25rem;
        }

        .metric-label {
            color: var(--color-text-primary);
            font-weight: 600;
            line-height: 1.35;
        }

        .metric-note {
            color: var(--color-text-secondary);
            font-size: 0.82rem;
            margin-top: 0.35rem;
            line-height: 1.5;
        }

        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--color-border);
            padding: 0.85rem;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-xs);
        }

        [data-testid="stMetric"] label {
            color: var(--color-text-secondary);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
            border-bottom: 1px solid var(--color-border);
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px 999px 0 0;
            padding: 0.45rem 0.85rem;
            background: #ffffff;
            border: 1px solid var(--color-border);
            border-bottom: none;
            color: var(--color-text-secondary);
        }

        .stTextArea textarea,
        .stTextInput input,
        .stNumberInput input,
        .stSelectbox div {
            border-radius: var(--radius-sm);
        }

        [data-testid="stDataFrame"] {
            border-radius: var(--radius-md);
            overflow: hidden;
        }

        .ops-footer {
            margin-top: 2.5rem;
            padding: 1.5rem 0 1.2rem 0;
            border-top: 1px solid var(--color-border);
            color: var(--color-text-secondary);
            font-size: 0.86rem;
        }

        .footer-grid {
            display: grid;
            grid-template-columns: 1.4fr 1fr 1fr 1fr;
            gap: 1.2rem;
        }

        .ops-footer b {
            color: var(--color-text-primary);
            font-weight: 600;
        }

        .footer-line {
            margin-top: 1.2rem;
            color: var(--color-text-tertiary);
            font-size: 0.78rem;
        }

        @media (max-width: 900px) {
            .footer-grid {
                grid-template-columns: 1fr;
            }

            .topbar {
                display: block;
            }

            .nav-note {
                margin-top: 0.7rem;
                display: inline-flex;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# SHARED COMPONENTS
# =============================================================================
def render_topbar() -> None:
    """Render the main website top navigation."""
    st.markdown(
        """
        <div class="topbar">
            <div class="brand">
                <div class="brand-logo">OI</div>
                <div>
                    <div class="brand-name">OpsIntel <span>AI</span></div>
                    <div class="brand-subtitle">Three AI applications for operations, cost, and hiring intelligence</div>
                </div>
            </div>
            <div class="nav-note">Professional SaaS interface</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav = st.columns(5)
    if nav[0].button("Home", use_container_width=True):
        go_to("Home")
    if nav[1].button("Why Us", use_container_width=True):
        go_to("Why Us")
    if nav[2].button("SupportOps", use_container_width=True):
        go_to("SupportOps Analyzer")
    if nav[3].button("CostOps", use_container_width=True):
        go_to("CostOps Analyzer")
    if nav[4].button("NextHire AI", use_container_width=True):
        go_to("NextHire AI")


def render_footer() -> None:
    """Render the footer."""
    st.markdown(
        """
        <div class="ops-footer">
            <div class="footer-grid">
                <div>
                    <b>OpsIntel AI</b><br>
                    Modular AI platform that turns uploaded business data into insights, risk signals, and action plans.
                </div>
                <div>
                    <b>Applications</b><br>
                    SupportOps Analyzer<br>
                    CostOps Analyzer<br>
                    NextHire AI
                </div>
                <div>
                    <b>Outputs</b><br>
                    Risk scores<br>
                    Savings opportunities<br>
                    Manager-ready reports
                </div>
                <div>
                    <b>Built With</b><br>
                    Python • Pandas • Streamlit<br>
                    Plotly charts<br>
                    Rule-based AI agents
                </div>
            </div>
            <div class="footer-line">
                Portfolio project by Saravanakumar Subramanian · Demo data only · Human review recommended before business decisions
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_module_header(kicker: str, title: str, copy: str) -> None:
    """Render a module header."""
    st.markdown(
        f"""
        <div class="module-header">
            <div class="module-kicker">{kicker}</div>
            <div class="module-title">{title}</div>
            <div class="module-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# SUPPORTOPS HELPERS
# =============================================================================
@st.cache_data
def load_default_support_data() -> pd.DataFrame:
    """Load generated support ticket demo data."""
    if not DATA_PATH.exists():
        st.error("Data file not found. Run this first: python app/data_generator.py")
        st.stop()
    return pd.read_csv(DATA_PATH)


def get_support_data(uploaded_file):
    """Return uploaded support data or demo support data."""
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file), f"Uploaded file: {uploaded_file.name}"

    if st.session_state.get("support_demo_enabled", False):
        return load_default_support_data(), "Demo support ticket dataset"

    return None, None


def prepare_support_analysis(raw_df: pd.DataFrame):
    """Validate and score support data."""
    raw_df = clean_support_ticket_data(raw_df)
    column_check = validate_required_columns(raw_df)

    if not column_check["passed"]:
        return raw_df, None, column_check

    filtered_df = raw_df.copy()
    scored_df = add_risk_score(filtered_df)
    return filtered_df, scored_df, column_check


# =============================================================================
# COSTOPS HELPERS
# =============================================================================
@st.cache_data
def load_cost_demo_data() -> pd.DataFrame:
    """Create demo cost dataset."""
    rows = [
        ["2026-01-01", "IT", "Cloud Compute", "AWS", 42000, 51500, "Cloud Platform", "US", "Ravi", "Technology"],
        ["2026-01-01", "IT", "SaaS Subscriptions", "Salesforce", 28000, 32200, "CRM", "US", "Anita", "Technology"],
        ["2026-01-01", "Operations", "Logistics", "FedEx", 36000, 39800, "Delivery Ops", "US", "Kim", "Operations"],
        ["2026-01-01", "Marketing", "Paid Ads", "Google Ads", 25000, 34500, "Demand Gen", "US", "Nora", "Growth"],
        ["2026-02-01", "IT", "Cloud Compute", "AWS", 42000, 54800, "Cloud Platform", "US", "Ravi", "Technology"],
        ["2026-02-01", "IT", "SaaS Subscriptions", "Salesforce", 28000, 33600, "CRM", "US", "Anita", "Technology"],
        ["2026-02-01", "Operations", "Logistics", "FedEx", 36000, 36500, "Delivery Ops", "US", "Kim", "Operations"],
        ["2026-02-01", "Marketing", "Paid Ads", "Google Ads", 25000, 37000, "Demand Gen", "US", "Nora", "Growth"],
        ["2026-03-01", "IT", "Cloud Compute", "AWS", 42000, 60300, "Cloud Platform", "US", "Ravi", "Technology"],
        ["2026-03-01", "Finance", "Consulting", "Deloitte", 18000, 28500, "Controls", "US", "Leah", "Corporate"],
        ["2026-03-01", "Operations", "Logistics", "FedEx", 36000, 42000, "Delivery Ops", "US", "Kim", "Operations"],
        ["2026-03-01", "Marketing", "Paid Ads", "Google Ads", 25000, 41500, "Demand Gen", "US", "Nora", "Growth"],
        ["2026-04-01", "IT", "Cloud Compute", "AWS", 42000, 63500, "Cloud Platform", "US", "Ravi", "Technology"],
        ["2026-04-01", "HR", "Recruiting Tools", "LinkedIn", 12000, 18500, "Hiring", "US", "Maya", "People"],
        ["2026-04-01", "Finance", "Consulting", "Deloitte", 18000, 24500, "Controls", "US", "Leah", "Corporate"],
        ["2026-04-01", "Marketing", "Paid Ads", "Google Ads", 25000, 39000, "Demand Gen", "US", "Nora", "Growth"],
    ]

    return pd.DataFrame(
        rows,
        columns=[
            "date",
            "department",
            "cost_category",
            "vendor",
            "budget_amount",
            "actual_amount",
            "project_name",
            "region",
            "owner",
            "business_unit",
        ],
    )


def analyze_cost_data(df: pd.DataFrame) -> pd.DataFrame:
    """Add CostOps analytics fields."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["variance"] = df["actual_amount"] - df["budget_amount"]
    df["variance_pct"] = (df["variance"] / df["budget_amount"] * 100).round(1)
    df["savings_opportunity"] = df["variance"].apply(lambda x: max(x * 0.45, 0)).round(0)
    df["risk_level"] = pd.cut(
        df["variance_pct"],
        bins=[-999, 5, 15, 999],
        labels=["Low", "Medium", "High"],
    ).astype(str)
    return df


def generate_cost_report(df: pd.DataFrame) -> str:
    """Generate a CostOps report."""
    total_spend = df["actual_amount"].sum()
    total_budget = df["budget_amount"].sum()
    variance = total_spend - total_budget
    savings = df["savings_opportunity"].sum()
    top_department = df.groupby("department")["variance"].sum().sort_values(ascending=False).index[0]
    top_vendor = df.groupby("vendor")["actual_amount"].sum().sort_values(ascending=False).index[0]

    return f"""OpsIntel AI - CostOps Manager Briefing

Total Actual Spend: ${total_spend:,.0f}
Total Budget: ${total_budget:,.0f}
Budget Variance: ${variance:,.0f}
Estimated Savings Opportunity: ${savings:,.0f}

Top Overspending Department:
- {top_department}

Highest Spend Vendor:
- {top_vendor}

Recommended Actions:
1. Review high-variance departments above 15%.
2. Renegotiate or consolidate high-spend vendor contracts.
3. Audit recurring SaaS and cloud usage.
4. Set a variance alert threshold at 10%.
5. Track owner-level accountability for repeated over-budget categories.

Note: Savings are demo estimates based on reducing avoidable variance by 45%.
"""


# =============================================================================
# NEXTHIRE HELPERS
# =============================================================================
DEMO_RESUME = """
Saravanakumar Subramanian
Business Analyst / Operations Analyst

Experience:
- Built dashboards using Excel, Power BI, Python, Pandas, and Streamlit.
- Worked with stakeholders to document business requirements and process improvements.
- Used SQL for data analysis and reporting.
- Created project documentation, KPI reports, and workflow analysis.
- Experience with Salesforce, Ansys, technical presentations, and customer-facing roles.

Education:
MS Engineering Management, Robert Morris University
BE Mechanical Engineering, Anna University
"""

DEMO_JD = """
Business Analyst - AI Operations Platform

Responsibilities:
- Gather and document business requirements.
- Analyze operational data using SQL, Excel, Python, and dashboards.
- Build reports for SLA, cost, customer experience, and workflow performance.
- Partner with stakeholders to improve process efficiency.
- Use Power BI, Tableau, or Streamlit to present insights.
- Identify automation opportunities and prepare executive summaries.

Required skills:
SQL, Excel, Python, Power BI, Tableau, Pandas, Streamlit, requirements gathering,
stakeholder management, KPI reporting, process improvement, data visualization,
business analysis, documentation, communication.
"""


def extract_keywords(text: str) -> Counter:
    """Extract rough keywords from text."""
    words = re.findall(r"[A-Za-z][A-Za-z\+\#\.]{1,}", text.lower())
    stop = {
        "and", "the", "for", "with", "using", "use", "to", "of", "in", "a", "an", "or", "by",
        "from", "on", "as", "is", "are", "be", "this", "that", "business", "analyst",
        "responsibilities", "required", "skills", "experience", "education",
    }
    keywords = [w for w in words if w not in stop and len(w) > 2]
    return Counter(keywords)


def analyze_resume_match(resume_text: str, jd_text: str):
    """Compare resume and job description keyword coverage."""
    resume_words = set(extract_keywords(resume_text).keys())
    jd_counter = extract_keywords(jd_text)
    jd_keywords = [word for word, _ in jd_counter.most_common(35)]

    matched = [word for word in jd_keywords if word in resume_words]
    missing = [word for word in jd_keywords if word not in resume_words]

    score = int(round((len(matched) / max(len(jd_keywords), 1)) * 100))
    return score, matched, missing


def generate_nexthire_report(score: int, matched: list[str], missing: list[str]) -> str:
    """Generate a candidate readiness report."""
    return f"""OpsIntel AI - NextHire Candidate Report

Resume-Job Match Score: {score}/100

Matched Keywords:
{", ".join(matched[:20])}

Missing / Weak Keywords:
{", ".join(missing[:20])}

Recommended Resume Improvements:
1. Add missing job keywords naturally into experience bullets.
2. Show measurable impact with numbers, such as time saved, cost reduced, or reports automated.
3. Add a technical skills section with SQL, Python, Excel, BI tools, and dashboarding tools.
4. Add one project bullet showing end-to-end analysis from raw data to recommendation.
5. Prepare interview examples for stakeholder management, process improvement, and KPI reporting.

Interview Prep Questions:
1. Tell me about a time you improved a business process.
2. How do you gather requirements from stakeholders?
3. How would you analyze SLA or cost performance data?
4. What dashboards or reports have you built?
5. How do you communicate insights to non-technical users?
"""


# =============================================================================
# PAGES
# =============================================================================
def render_home_page() -> None:
    """Render home page."""
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">OpsIntel AI · Three Application Platform</div>
            <div class="hero-title">
                One professional platform for <span>operations, cost, and hiring intelligence.</span>
            </div>
            <div class="hero-copy">
                Upload business data and turn it into risk signals, savings opportunities,
                skill-gap insights, AI recommendations, and manager-ready reports.
            </div>
            <div class="mini-proof-row">
                <div class="proof-pill">SupportOps risk detection</div>
                <div class="proof-pill">CostOps savings analysis</div>
                <div class="proof-pill">NextHire skill-gap scoring</div>
                <div class="proof-pill">Downloadable reports</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Choose one application</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Three modules. Clean navigation. Each application has its own workflow.</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="app-card">
                <div class="icon-box sage">🎧</div>
                <div class="app-title">SupportOps Analyzer</div>
                <div class="app-copy">
                    Analyze support tickets for SLA breaches, customer frustration, escalation risk,
                    agent workload, and root-cause issues.
                </div>
                <div class="value-list">
                    • Reduce escalation rework<br>
                    • Prioritize risky tickets<br>
                    • Generate manager briefings
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open SupportOps", key="home_support", use_container_width=True):
            go_to("SupportOps Analyzer")

    with col2:
        st.markdown(
            """
            <div class="app-card">
                <div class="icon-box amber">💰</div>
                <div class="app-title">CostOps Analyzer</div>
                <div class="app-copy">
                    Analyze budgets, actual spend, vendors, departments, cost anomalies,
                    and estimated savings opportunities.
                </div>
                <div class="value-list">
                    • Detect overspending<br>
                    • Find avoidable variance<br>
                    • Prioritize savings actions
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open CostOps", key="home_cost", use_container_width=True):
            go_to("CostOps Analyzer")

    with col3:
        st.markdown(
            """
            <div class="app-card">
                <div class="icon-box">🧠</div>
                <div class="app-title">NextHire AI</div>
                <div class="app-copy">
                    Compare resumes with job descriptions, calculate match score,
                    identify skill gaps, and generate interview preparation.
                </div>
                <div class="value-list">
                    • Reduce screening time<br>
                    • Improve candidate fit<br>
                    • Generate readiness reports
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open NextHire AI", key="home_hire", use_container_width=True):
            go_to("NextHire AI")

    render_footer()


def render_why_us_page() -> None:
    """Render Why Us page."""
    render_module_header(
        "WHY OPSINTEL AI",
        "Find money leaks, reduce manual review, and turn data into decisions.",
        "OpsIntel AI is built around a simple idea: companies already have useful operational data, but teams lose time and money when that data is not translated into action quickly.",
    )

    st.markdown('<div class="section-title">How the platform can help save money</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">These are example business-impact estimates. Actual savings depend on company size, data quality, process maturity, and implementation discipline.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-number">5–15%</div>
                <div class="metric-label">Potential support rework reduction</div>
                <div class="metric-note">
                    By identifying SLA breaches, repeat contacts, and high-risk tickets earlier, teams may reduce escalation handling and manual follow-up.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-number">8–12%</div>
                <div class="metric-label">Potential avoidable spend discovery</div>
                <div class="metric-note">
                    CostOps can highlight budget variance, unused subscriptions, vendor concentration, and recurring overspend patterns.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-number">30–50%</div>
                <div class="metric-label">Manual screening time reduction</div>
                <div class="metric-note">
                    NextHire AI can pre-score resumes against job descriptions so recruiters and candidates can focus on fit faster.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Simple ROI example</div>', unsafe_allow_html=True)

    roi_cols = st.columns(3)
    monthly_cost = roi_cols[0].number_input("Monthly operational cost reviewed ($)", min_value=1000, value=50000, step=1000)
    avoidable_pct = roi_cols[1].slider("Estimated avoidable waste found (%)", min_value=1, max_value=20, value=8)
    time_saved_hours = roi_cols[2].slider("Manual review hours saved / month", min_value=1, max_value=100, value=20)

    monthly_savings = monthly_cost * avoidable_pct / 100
    labor_savings = time_saved_hours * 35
    total_value = monthly_savings + labor_savings

    r1, r2, r3 = st.columns(3)
    r1.metric("Estimated cost savings", f"${monthly_savings:,.0f}/mo")
    r2.metric("Estimated labor value", f"${labor_savings:,.0f}/mo")
    r3.metric("Total estimated value", f"${total_value:,.0f}/mo")

    st.info("This ROI calculator is a portfolio demo. It shows business value thinking, not a guaranteed financial result.")

    render_footer()


def render_supportops_page() -> None:
    """Render SupportOps Analyzer."""
    render_module_header(
        "APPLICATION 1",
        "SupportOps Analyzer",
        "Upload support ticket data or use the demo dataset to detect SLA risk, customer frustration, escalation patterns, and action priorities.",
    )

    uploaded_file = st.file_uploader("Upload support ticket CSV", type=["csv"], help="Upload a CSV with support ticket fields.")

    action_cols = st.columns(2)
    if action_cols[0].button("Use demo support data", use_container_width=True):
        enable_support_demo()

    if action_cols[1].button("Clear support demo", use_container_width=True):
        st.session_state["support_demo_enabled"] = False
        st.rerun()

    raw_df, data_source = get_support_data(uploaded_file)

    if raw_df is None:
        st.info("Upload a support CSV or click **Use demo support data** to start.")
        st.subheader("Required columns")
        st.code(", ".join(REQUIRED_COLUMNS))
        return

    filtered_df, scored_df, column_check = prepare_support_analysis(raw_df)

    support_tabs = st.tabs(["Validate", "Overview", "SLA & Risk", "Agents", "Report", "Raw Data"])

    with support_tabs[0]:
        st.subheader("Data Validation")
        col1, col2, col3 = st.columns(3)
        col1.write("**Data Source**")
        col1.write(data_source)
        col2.metric("Rows", f"{len(raw_df):,}")
        col3.metric("Columns", f"{len(raw_df.columns):,}")

        if column_check["passed"]:
            st.success("Required column check passed.")
        else:
            st.error("Required column check failed.")
            st.write(column_check["missing_columns"])
            st.stop()

        quality = data_quality_report(clean_support_ticket_data(raw_df))
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Quality Score", f"{quality['quality_score']}/100")
        q2.metric("Missing Values", quality["missing_value_total"])
        q3.metric("Duplicate IDs", quality["duplicate_ticket_count"])
        q4.metric("Invalid Dates", quality["invalid_date_count"])

    with support_tabs[1]:
        st.subheader("Executive Summary")
        kpis = calculate_kpis(filtered_df)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Tickets", f"{kpis['total_tickets']:,}")
        col2.metric("Open Tickets", f"{kpis['open_tickets']:,}")
        col3.metric("SLA Breach Rate", f"{kpis['sla_breach_rate']}%")
        col4.metric("Avg Resolution", f"{kpis['avg_resolution_hours']} hrs")

        col5, col6, col7, col8 = st.columns(4)
        col5.metric("Escalated", f"{kpis['escalated_tickets']:,}")
        col6.metric("Avg Rating", f"{kpis['avg_customer_rating']}/5")
        col7.metric("High Risk", f"{kpis['high_risk_tickets']:,}")
        col8.metric("Negative Sentiment", f"{kpis['negative_sentiment_rate']}%")

        issue_summary = issue_type_summary(filtered_df)
        fig = px.bar(issue_summary, x="issue_type", y="total_tickets", title="Ticket Volume by Issue Type", text="total_tickets")
        st.plotly_chart(fig, use_container_width=True)

    with support_tabs[2]:
        st.subheader("SLA & Escalation Risk")
        dept_sla = sla_summary_by_department(filtered_df)
        fig = px.bar(dept_sla, x="department", y="sla_breach_rate", title="SLA Breach Rate by Department", text="sla_breach_rate")
        st.plotly_chart(fig, use_container_width=True)

        risk_counts = scored_df["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["risk_level", "count"]
        fig = px.bar(risk_counts, x="risk_level", y="count", title="Escalation Risk Levels", text="count")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Top High-Risk Tickets")
        st.dataframe(top_high_risk_tickets(filtered_df), use_container_width=True)

    with support_tabs[3]:
        agent_subtabs = st.tabs(["AI Ticket Triage", "Daily Briefing", "Agent Performance"])

        with agent_subtabs[0]:
            st.subheader("AI Ticket Triage Agent")
            ticket_options = scored_df["ticket_id"].tolist()
            selected_ticket_id = st.selectbox("Select a ticket", ticket_options)
            selected_ticket = scored_df[scored_df["ticket_id"] == selected_ticket_id].iloc[0]

            if st.button("Analyze Selected Ticket", use_container_width=True):
                agent_result = analyze_ticket(selected_ticket)
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Risk Score", f"{agent_result['risk_score']}/100")
                col2.metric("Risk Level", agent_result["risk_level"])
                col3.metric("SLA Status", agent_result["sla_status"])
                col4.metric("Urgency", agent_result["urgency"])

                st.write(f"**Recommended Action:** {agent_result['recommended_action']}")
                st.write(f"**Routing:** {agent_result['routing_recommendation']}")
                st.write(f"**Business Impact:** {agent_result['business_impact']}")

                st.subheader("Customer Response Draft")
                st.write(agent_result["customer_response_draft"])

                st.subheader("Agent Trace")
                for step in agent_result["agent_trace"]:
                    st.write(f"✅ {step}")

        with agent_subtabs[1]:
            st.subheader("Daily SupportOps AI Briefing")
            briefing = generate_daily_briefing(scored_df)
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

        with agent_subtabs[2]:
            st.subheader("Agent Performance")
            agent_summary = agent_performance_summary(filtered_df)
            fig = px.bar(agent_summary, x="agent", y="total_tickets", title="Ticket Workload by Agent", text="total_tickets")
            st.plotly_chart(fig, use_container_width=True)
            fig = px.bar(agent_summary, x="agent", y="sla_breach_rate", title="SLA Breach Rate by Agent", text="sla_breach_rate")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(agent_summary, use_container_width=True)

    with support_tabs[4]:
        st.subheader("Download SupportOps Report")
        report_text = generate_briefing_text(scored_df)
        st.text_area("Report Preview", report_text, height=360)
        st.download_button(
            "Download SupportOps Manager Report",
            data=report_text,
            file_name="supportops_manager_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with support_tabs[5]:
        st.subheader("Raw Support Ticket Data")
        st.dataframe(scored_df, use_container_width=True)


def render_costops_page() -> None:
    """Render CostOps Analyzer."""
    render_module_header(
        "APPLICATION 2",
        "CostOps Analyzer",
        "Analyze spend, budget variance, vendor concentration, cost anomalies, and estimated savings opportunities.",
    )

    uploaded_file = st.file_uploader("Upload cost CSV", type=["csv"], help="Optional. Use the demo data if you do not have a cost file.")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        data_source = f"Uploaded file: {uploaded_file.name}"
    else:
        df = load_cost_demo_data()
        data_source = "Demo cost dataset"

    required = {"date", "department", "cost_category", "vendor", "budget_amount", "actual_amount"}
    missing = required - set(df.columns)

    if missing:
        st.error(f"Missing required columns: {sorted(missing)}")
        st.code("date, department, cost_category, vendor, budget_amount, actual_amount")
        return

    df = analyze_cost_data(df)

    st.caption(f"Data source: {data_source}")

    total_spend = df["actual_amount"].sum()
    total_budget = df["budget_amount"].sum()
    variance = total_spend - total_budget
    savings = df["savings_opportunity"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Actual Spend", f"${total_spend:,.0f}")
    c2.metric("Budget", f"${total_budget:,.0f}")
    c3.metric("Over Budget", f"${variance:,.0f}")
    c4.metric("Est. Savings Opportunity", f"${savings:,.0f}")

    tabs = st.tabs(["Spend Overview", "Departments & Vendors", "Savings Report", "Raw Data"])

    with tabs[0]:
        monthly = df.groupby("date", as_index=False)[["budget_amount", "actual_amount"]].sum()
        fig = px.line(monthly, x="date", y=["budget_amount", "actual_amount"], title="Budget vs Actual Spend Trend", markers=True)
        st.plotly_chart(fig, use_container_width=True)

        fig = px.bar(df, x="cost_category", y="variance", color="risk_level", title="Cost Variance by Category", text="variance")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        dept = df.groupby("department", as_index=False)[["budget_amount", "actual_amount", "variance", "savings_opportunity"]].sum()
        fig = px.bar(dept, x="department", y="variance", title="Budget Variance by Department", text="variance")
        st.plotly_chart(fig, use_container_width=True)

        vendor = df.groupby("vendor", as_index=False)["actual_amount"].sum().sort_values("actual_amount", ascending=False)
        fig = px.pie(vendor, names="vendor", values="actual_amount", title="Vendor Spend Concentration")
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(dept, use_container_width=True)

    with tabs[2]:
        report = generate_cost_report(df)
        st.text_area("CostOps Report Preview", report, height=360)
        st.download_button(
            "Download CostOps Report",
            data=report,
            file_name="costops_savings_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with tabs[3]:
        st.dataframe(df, use_container_width=True)


def render_nexthire_page() -> None:
    """Render NextHire AI."""
    render_module_header(
        "APPLICATION 3",
        "NextHire AI",
        "Compare a resume with a job description, calculate match score, identify missing keywords, and generate interview prep.",
    )

    input_cols = st.columns(2)
    with input_cols[0]:
        resume_text = st.text_area("Resume text", value=DEMO_RESUME, height=330)
    with input_cols[1]:
        jd_text = st.text_area("Job description", value=DEMO_JD, height=330)

    if not resume_text.strip() or not jd_text.strip():
        st.warning("Paste both resume text and job description to analyze.")
        return

    score, matched, missing = analyze_resume_match(resume_text, jd_text)

    c1, c2, c3 = st.columns(3)
    c1.metric("Resume-JD Match Score", f"{score}/100")
    c2.metric("Matched Keywords", len(matched))
    c3.metric("Missing Keywords", len(missing))

    tabs = st.tabs(["Skill Match", "Suggestions", "Interview Prep", "Report"])

    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Matched Keywords")
            st.write(", ".join(matched[:30]) if matched else "No strong matches found.")
        with col2:
            st.subheader("Missing / Weak Keywords")
            st.write(", ".join(missing[:30]) if missing else "No major missing keywords found.")

        chart_df = pd.DataFrame({"category": ["Matched", "Missing"], "count": [len(matched), len(missing)]})
        fig = px.bar(chart_df, x="category", y="count", title="Resume Keyword Coverage", text="count")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.subheader("Resume Improvement Suggestions")
        suggestions = [
            "Add missing job keywords naturally into experience bullets.",
            "Use measurable outcomes such as reduced time, improved accuracy, automated reports, or cost savings.",
            "Add a technical skills section with SQL, Python, Excel, BI tools, and dashboarding tools.",
            "Show one end-to-end analytics project from raw data to recommendation.",
            "Add stakeholder-facing language: requirements gathering, documentation, process improvement, KPI reporting.",
        ]
        for idx, suggestion in enumerate(suggestions, start=1):
            st.write(f"{idx}. {suggestion}")

    with tabs[2]:
        st.subheader("Interview Prep Questions")
        questions = [
            "Tell me about a time you improved a business process.",
            "How do you gather and document requirements from stakeholders?",
            "How would you analyze SLA or cost performance data?",
            "What dashboards or reports have you built?",
            "How do you explain technical findings to non-technical users?",
            "What would you do if stakeholders disagree on requirements?",
        ]
        for idx, question in enumerate(questions, start=1):
            st.write(f"{idx}. {question}")

    with tabs[3]:
        report = generate_nexthire_report(score, matched, missing)
        st.text_area("Candidate Report Preview", report, height=360)
        st.download_button(
            "Download NextHire Candidate Report",
            data=report,
            file_name="nexthire_candidate_report.txt",
            mime="text/plain",
            use_container_width=True,
        )


# =============================================================================
# MAIN APP
# =============================================================================
load_css()
render_topbar()

page = st.session_state.get("page", "Home")

if page == "Home":
    render_home_page()
elif page == "Why Us":
    render_why_us_page()
elif page == "SupportOps Analyzer":
    render_supportops_page()
elif page == "CostOps Analyzer":
    render_costops_page()
elif page == "NextHire AI":
    render_nexthire_page()
else:
    render_home_page()
