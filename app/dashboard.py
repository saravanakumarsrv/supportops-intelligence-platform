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
import json
import os
import re
import sys
from collections import Counter

from google import genai

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

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
    "process_demo_enabled": False,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


PAGE_TO_SLUG = {
    "Home": "home",
    "Why Us": "why-us",
    "SupportOps Analyzer": "supportops",
    "CostOps Analyzer": "costops",
    "NextHire AI": "nexthire",
    "ProcessOps Analyzer": "processops",
}

SLUG_TO_PAGE = {value: key for key, value in PAGE_TO_SLUG.items()}


def sync_page_from_query() -> None:
    """Sync smooth HTML navigation links with Streamlit session state."""
    try:
        raw_page = st.query_params.get("page", None)
        if isinstance(raw_page, list):
            raw_page = raw_page[0] if raw_page else None
        if raw_page in SLUG_TO_PAGE:
            st.session_state["page"] = SLUG_TO_PAGE[raw_page]
    except Exception:
        pass


def update_page_query(page_name: str) -> None:
    """Update the URL query parameter when navigating from Streamlit buttons."""
    try:
        st.query_params["page"] = PAGE_TO_SLUG.get(page_name, "home")
    except Exception:
        pass


def go_to(page_name: str) -> None:
    """Navigate to a main app page."""
    st.session_state["page"] = page_name
    update_page_query(page_name)
    st.rerun()


def enable_support_demo() -> None:
    """Enable demo support data and stay inside SupportOps."""
    st.session_state["support_demo_enabled"] = True
    st.session_state["page"] = "SupportOps Analyzer"
    update_page_query("SupportOps Analyzer")
    st.rerun()


def enable_process_demo() -> None:
    """Enable demo process data and stay inside ProcessOps."""
    st.session_state["process_demo_enabled"] = True
    st.session_state["page"] = "ProcessOps Analyzer"
    update_page_query("ProcessOps Analyzer")
    st.rerun()


# =============================================================================
# EMBEDDED PROFESSIONAL CSS
# =============================================================================
def load_css() -> None:
    """Load premium homepage/navigation CSS directly from this dashboard file."""
    st.markdown(
        """
        <style>
        :root {
            --color-primary: #3d3a8c;
            --color-primary-hover: #35327a;
            --color-primary-active: #2f2c6d;
            --color-primary-subtle: rgba(61, 58, 140, 0.08);
            --color-primary-soft: #efeff9;

            --color-accent: #8faf9b;
            --color-accent-subtle: rgba(143, 175, 155, 0.16);
            --color-amber: #9a7435;
            --color-amber-bg: #fbf4e8;
            --color-rose: #9b4a4a;
            --color-rose-bg: #fbeeee;

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
            --radius-2xl: 30px;
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
                radial-gradient(circle at top left, rgba(61, 58, 140, 0.075), transparent 30%),
                radial-gradient(circle at top right, rgba(143, 175, 155, 0.11), transparent 28%),
                linear-gradient(180deg, #ffffff 0%, #fafaf9 42%, #f3f1ec 100%);
            color: var(--color-text-primary);
            font-family: var(--font-sans);
        }

        .block-container {
            max-width: 1240px;
            padding-top: 0.65rem;
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
            0% { transform: translateY(0); }
            50% { transform: translateY(-7px); }
            100% { transform: translateY(0); }
        }

        @keyframes subtlePulse {
            0% { box-shadow: 0 0 0 0 rgba(143, 175, 155, 0.18); }
            60% { box-shadow: 0 0 0 8px rgba(143, 175, 155, 0); }
            100% { box-shadow: 0 0 0 0 rgba(143, 175, 155, 0); }
        }

        /* -----------------------------
           Top Navigation
        ----------------------------- */
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.95rem 0 0.95rem 0;
            border-bottom: 1px solid var(--color-border);
            margin-bottom: 0.72rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .brand-logo {
            width: 44px;
            height: 44px;
            border-radius: 14px;
            background:
                radial-gradient(circle at 32% 22%, rgba(255,255,255,0.72), transparent 22%),
                linear-gradient(135deg, #3d3a8c 0%, #6f6baa 54%, #8faf9b 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 700;
            font-size: 1rem;
            letter-spacing: -0.08em;
            box-shadow: 0 14px 30px rgba(61, 58, 140, 0.18);
            animation: softFloat 6s ease-in-out infinite;
        }

        .brand-name {
            font-size: 1.45rem;
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
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.43rem 0.78rem;
            border-radius: var(--radius-full);
            color: var(--color-primary);
            background: var(--color-primary-subtle);
            border: 1px solid rgba(61, 58, 140, 0.14);
            font-size: 0.82rem;
            font-weight: 600;
        }

        .nav-note-dot {
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: var(--color-accent);
            box-shadow: 0 0 0 4px rgba(143, 175, 155, 0.16);
            animation: subtlePulse 2.4s ease-in-out infinite;
        }

        .nav-helper {
            color: var(--color-text-tertiary);
            font-size: 0.78rem;
            margin-bottom: 0.55rem;
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

        /* -----------------------------
           Homepage Hero
        ----------------------------- */
        .hero-shell {
            margin-top: 0.95rem;
            animation: fadeUp 0.65s ease-out;
        }

        .hero-panel {
            position: relative;
            min-height: 514px;
            padding: 3.05rem 2.55rem;
            border-radius: var(--radius-2xl);
            background:
                radial-gradient(circle at 84% 18%, rgba(61, 58, 140, 0.10), transparent 32%),
                radial-gradient(circle at 10% 88%, rgba(143, 175, 155, 0.13), transparent 32%),
                linear-gradient(135deg, #ffffff 0%, #fafaf9 55%, #f3f1ec 100%);
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-md);
            overflow: hidden;
        }

        .hero-panel::after {
            content: "";
            position: absolute;
            width: 270px;
            height: 270px;
            border-radius: 50%;
            right: -95px;
            top: -95px;
            background: radial-gradient(circle, rgba(61,58,140,0.10), transparent 68%);
            animation: softFloat 8s ease-in-out infinite;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.42rem 0.82rem;
            border-radius: var(--radius-full);
            color: var(--color-primary);
            background: var(--color-primary-subtle);
            border: 1px solid rgba(61, 58, 140, 0.14);
            font-weight: 650;
            font-size: 0.78rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 1.05rem;
        }

        .hero-title {
            color: var(--color-text-primary);
            font-size: clamp(2.45rem, 5vw, 4.55rem);
            line-height: 1.01;
            font-weight: 650;
            letter-spacing: -0.055em;
            max-width: 690px;
            margin-bottom: 1rem;
        }

        .hero-title span {
            background: linear-gradient(90deg, #3d3a8c, #6f6baa, #557c5f);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero-copy {
            color: var(--color-text-secondary);
            font-size: 1.07rem;
            line-height: 1.72;
            max-width: 620px;
            margin-bottom: 1.15rem;
        }

        .tech-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.58rem;
            margin-top: 1.15rem;
        }

        .tech-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;
            padding: 0.52rem 0.72rem;
            border-radius: 10px;
            background: #ffffff;
            border: 1px solid var(--color-border);
            color: var(--color-text-secondary);
            font-size: 0.83rem;
            font-weight: 500;
            box-shadow: var(--shadow-xs);
        }

        .tech-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--color-primary);
        }

        .tech-dot.sage {
            background: var(--color-accent);
        }

        .tech-dot.amber {
            background: var(--color-amber);
        }

        .hero-cta-note {
            color: var(--color-text-tertiary);
            font-size: 0.82rem;
            margin-top: 0.72rem;
        }

        /* -----------------------------
           Dashboard mockup
        ----------------------------- */
        .dashboard-preview-card {
            min-height: 514px;
            padding: 1rem;
            border-radius: var(--radius-2xl);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-lg);
            overflow: hidden;
            animation: fadeUp 0.8s ease-out;
        }

        .dashboard-browser {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.45rem 0.9rem 0.45rem;
            border-bottom: 1px solid var(--color-border);
            margin-bottom: 0.85rem;
        }

        .browser-dot {
            width: 9px;
            height: 9px;
            border-radius: 999px;
            background: #ddd8cf;
        }

        .browser-dot.red { background: #df8f83; }
        .browser-dot.amber { background: #d8b36f; }
        .browser-dot.green { background: #8faf9b; }

        .browser-url {
            margin-left: auto;
            margin-right: auto;
            padding: 0.28rem 2rem;
            border-radius: 999px;
            background: var(--color-bg-soft);
            color: var(--color-text-tertiary);
            font-size: 0.74rem;
        }

        .mock-layout {
            display: grid;
            grid-template-columns: 54px 1fr;
            gap: 0.85rem;
        }

        .mock-sidebar {
            min-height: 420px;
            border-radius: 16px;
            background: linear-gradient(180deg, #3d3a8c 0%, #2f2c6d 100%);
            padding: 0.55rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.65rem;
        }

        .mock-side-icon {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            color: rgba(255,255,255,0.82);
            font-size: 0.9rem;
        }

        .mock-side-icon.active {
            background: rgba(255,255,255,0.16);
            color: #ffffff;
        }

        .mock-avatar {
            margin-top: auto;
            width: 34px;
            height: 34px;
            border-radius: 999px;
            background: #eff5f1;
            color: #557c5f;
            display: grid;
            place-items: center;
            font-size: 0.72rem;
            font-weight: 700;
        }

        .mock-main {
            min-width: 0;
        }

        .mock-topline {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }

        .mock-title {
            color: var(--color-text-primary);
            font-size: 1rem;
            font-weight: 650;
        }

        .mock-sub {
            color: var(--color-text-tertiary);
            font-size: 0.75rem;
        }

        .mock-date {
            padding: 0.43rem 0.65rem;
            border: 1px solid var(--color-border);
            border-radius: 10px;
            color: var(--color-text-secondary);
            font-size: 0.72rem;
            background: #ffffff;
        }

        .mock-kpis {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.58rem;
            margin-bottom: 0.78rem;
        }

        .mock-kpi {
            padding: 0.72rem;
            border: 1px solid var(--color-border);
            border-radius: 12px;
            background: #ffffff;
        }

        .mock-kpi-label {
            color: var(--color-text-tertiary);
            font-size: 0.68rem;
            margin-bottom: 0.28rem;
        }

        .mock-kpi-value {
            color: var(--color-text-primary);
            font-size: 1.2rem;
            font-weight: 650;
            letter-spacing: -0.03em;
        }

        .mock-kpi-good {
            display: inline-flex;
            margin-top: 0.38rem;
            padding: 0.16rem 0.36rem;
            border-radius: 999px;
            background: var(--color-success-bg);
            color: var(--color-success);
            font-size: 0.64rem;
            font-weight: 600;
        }

        .mock-lower {
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 0.75rem;
        }

        .mock-chart-card,
        .mock-activity-card {
            border: 1px solid var(--color-border);
            border-radius: 14px;
            background: #ffffff;
            padding: 0.85rem;
            min-height: 205px;
        }

        .mock-card-heading {
            font-size: 0.82rem;
            font-weight: 650;
            color: var(--color-text-primary);
            margin-bottom: 0.55rem;
        }

        .mock-chart {
            height: 140px;
            border-radius: 12px;
            border: 1px solid var(--color-border);
            background:
                linear-gradient(180deg, rgba(61, 58, 140, 0.05), transparent),
                repeating-linear-gradient(
                    to right,
                    transparent 0,
                    transparent 38px,
                    rgba(232, 231, 227, 0.62) 38px,
                    rgba(232, 231, 227, 0.62) 39px
                );
            position: relative;
            overflow: hidden;
        }

        .mock-chart::before {
            content: "";
            position: absolute;
            left: 18px;
            right: 18px;
            top: 62px;
            height: 3px;
            border-radius: 999px;
            background: linear-gradient(90deg, #3d3a8c, #6f6baa, #8faf9b);
            transform: skewY(-7deg);
            box-shadow:
                42px -18px 0 -1px rgba(61,58,140,0.72),
                96px 13px 0 -1px rgba(143,175,155,0.72),
                145px -12px 0 -1px rgba(154,116,53,0.46);
        }

        .mock-activity {
            display: grid;
            gap: 0.55rem;
        }

        .mock-activity-row {
            display: grid;
            grid-template-columns: 24px 1fr auto;
            gap: 0.45rem;
            align-items: center;
        }

        .mock-activity-icon {
            width: 24px;
            height: 24px;
            border-radius: 8px;
            display: grid;
            place-items: center;
            background: var(--color-primary-subtle);
            color: var(--color-primary);
            font-size: 0.72rem;
        }

        .mock-activity-text {
            color: var(--color-text-secondary);
            font-size: 0.72rem;
        }

        .mock-activity-time {
            color: var(--color-text-tertiary);
            font-size: 0.66rem;
        }

        .mock-link {
            color: var(--color-primary);
            font-size: 0.76rem;
            font-weight: 600;
            margin-top: 0.8rem;
        }

        /* -----------------------------
           Homepage sections
        ----------------------------- */
        .section-title {
            margin-top: 2rem;
            margin-bottom: 0.85rem;
            color: var(--color-text-primary);
            font-size: 1.62rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            text-align: center;
        }

        .section-copy {
            color: var(--color-text-secondary);
            margin-top: -0.4rem;
            margin-bottom: 1rem;
            line-height: 1.65;
            text-align: center;
        }

        .app-card {
            padding: 1.4rem;
            border-radius: var(--radius-lg);
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
            min-height: 268px;
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

        .app-card-top {
            display: grid;
            grid-template-columns: 58px 1fr;
            gap: 1rem;
            align-items: start;
        }

        .icon-box {
            width: 54px;
            height: 54px;
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.35rem;
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
            font-size: 1.18rem;
            font-weight: 650;
            margin-bottom: 0.38rem;
        }

        .app-copy {
            color: var(--color-text-secondary);
            line-height: 1.55;
            font-size: 0.92rem;
        }

        .value-list {
            color: var(--color-primary);
            font-size: 0.86rem;
            margin-top: 0.95rem;
            line-height: 1.65;
            font-weight: 500;
        }

        .home-impact-strip {
            margin-top: 1.4rem;
            padding: 1.2rem;
            border: 1px solid var(--color-border);
            border-radius: var(--radius-lg);
            background: rgba(255,255,255,0.72);
            box-shadow: var(--shadow-xs);
        }

        .impact-title {
            text-align: center;
            color: var(--color-text-primary);
            font-size: 1rem;
            font-weight: 650;
            margin-bottom: 1rem;
        }

        .impact-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.8rem;
        }

        .impact-item {
            display: grid;
            grid-template-columns: 42px 1fr;
            gap: 0.8rem;
            align-items: center;
            padding: 0.8rem;
            border-radius: var(--radius-md);
            background: #ffffff;
            border: 1px solid var(--color-border);
        }

        .impact-icon {
            width: 42px;
            height: 42px;
            border-radius: 999px;
            display: grid;
            place-items: center;
            background: var(--color-success-bg);
            color: var(--color-success);
            font-size: 1rem;
        }

        .impact-number {
            color: var(--color-text-primary);
            font-size: 1.18rem;
            font-weight: 650;
            line-height: 1;
        }

        .impact-label {
            color: var(--color-text-secondary);
            font-size: 0.78rem;
            margin-top: 0.18rem;
        }

        /* -----------------------------
           Existing module pages
        ----------------------------- */
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


        /* -----------------------------
           Why Us Page Polish
        ----------------------------- */
        .why-hero-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
            gap: 1.1rem;
            margin-bottom: 1.25rem;
            animation: fadeUp 0.65s ease-out;
        }

        .why-hero-panel {
            padding: 2rem;
            border-radius: var(--radius-xl);
            background:
                radial-gradient(circle at 88% 18%, rgba(61, 58, 140, 0.10), transparent 30%),
                linear-gradient(135deg, #ffffff, #fafaf9);
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
        }

        .why-kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.38rem 0.72rem;
            border-radius: var(--radius-full);
            color: var(--color-primary);
            background: var(--color-primary-subtle);
            border: 1px solid rgba(61, 58, 140, 0.14);
            font-size: 0.76rem;
            font-weight: 650;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin-bottom: 0.9rem;
        }

        .why-title {
            color: var(--color-text-primary);
            font-size: clamp(2rem, 4vw, 3.15rem);
            line-height: 1.04;
            font-weight: 650;
            letter-spacing: -0.045em;
            margin-bottom: 0.85rem;
        }

        .why-title span {
            color: var(--color-primary);
        }

        .why-copy {
            color: var(--color-text-secondary);
            line-height: 1.72;
            font-size: 1rem;
            max-width: 700px;
        }

        .why-proof-card {
            padding: 1.35rem;
            border-radius: var(--radius-xl);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
            min-height: 100%;
        }

        .why-proof-title {
            color: var(--color-text-primary);
            font-size: 1rem;
            font-weight: 650;
            margin-bottom: 0.8rem;
        }

        .why-proof-list {
            display: grid;
            gap: 0.7rem;
        }

        .why-proof-row {
            display: grid;
            grid-template-columns: 34px 1fr;
            gap: 0.75rem;
            align-items: start;
            padding: 0.75rem;
            border-radius: var(--radius-md);
            background: var(--color-bg-soft);
            border: 1px solid var(--color-border);
        }

        .why-proof-icon {
            width: 34px;
            height: 34px;
            border-radius: 11px;
            display: grid;
            place-items: center;
            background: var(--color-primary-subtle);
            color: var(--color-primary);
            font-weight: 650;
        }

        .why-proof-row b {
            color: var(--color-text-primary);
            font-weight: 650;
        }

        .why-proof-row p {
            color: var(--color-text-secondary);
            margin: 0.15rem 0 0 0;
            font-size: 0.83rem;
            line-height: 1.45;
        }

        .value-card {
            padding: 1.25rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
            min-height: 236px;
            transition:
                transform var(--transition-medium),
                border-color var(--transition-medium),
                box-shadow var(--transition-medium);
        }

        .value-card:hover {
            transform: translateY(-3px);
            border-color: var(--color-border-hover);
            box-shadow: var(--shadow-md);
        }

        .value-icon {
            width: 46px;
            height: 46px;
            border-radius: var(--radius-md);
            display: grid;
            place-items: center;
            margin-bottom: 0.9rem;
            background: var(--color-primary-subtle);
            color: var(--color-primary);
            font-size: 1.1rem;
        }

        .value-icon.sage {
            background: var(--color-accent-subtle);
            color: var(--color-success);
        }

        .value-icon.amber {
            background: var(--color-warning-bg);
            color: var(--color-warning);
        }

        .value-number {
            color: var(--color-text-primary);
            font-size: 1.65rem;
            font-weight: 650;
            letter-spacing: -0.03em;
            margin-bottom: 0.2rem;
        }

        .value-label {
            color: var(--color-text-primary);
            font-weight: 650;
            line-height: 1.35;
            margin-bottom: 0.35rem;
        }

        .value-note {
            color: var(--color-text-secondary);
            font-size: 0.84rem;
            line-height: 1.52;
        }

        .cost-leak-panel {
            margin-top: 1.1rem;
            padding: 1.45rem;
            border-radius: var(--radius-xl);
            background:
                linear-gradient(135deg, rgba(61, 58, 140, 0.055), rgba(143, 175, 155, 0.075)),
                #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
        }

        .cost-leak-grid {
            display: grid;
            grid-template-columns: 0.95fr 1.05fr;
            gap: 1rem;
            align-items: stretch;
        }

        .cost-leak-title {
            color: var(--color-text-primary);
            font-size: 1.35rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            margin-bottom: 0.45rem;
        }

        .cost-leak-copy {
            color: var(--color-text-secondary);
            line-height: 1.62;
            font-size: 0.94rem;
        }

        .cost-row {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 1rem;
            padding: 0.78rem 0;
            border-bottom: 1px solid var(--color-border);
        }

        .cost-row:last-child {
            border-bottom: none;
        }

        .cost-row-label {
            color: var(--color-text-secondary);
            font-size: 0.88rem;
        }

        .cost-row-value {
            color: var(--color-primary);
            font-weight: 650;
            font-size: 0.92rem;
        }

        .roi-panel {
            margin-top: 1.25rem;
            padding: 1.45rem;
            border-radius: var(--radius-xl);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-md);
        }

        .roi-panel-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .roi-panel-title {
            color: var(--color-text-primary);
            font-size: 1.35rem;
            font-weight: 650;
            letter-spacing: -0.02em;
        }

        .roi-panel-subtitle {
            color: var(--color-text-secondary);
            font-size: 0.9rem;
            line-height: 1.55;
            margin-top: 0.25rem;
        }

        .roi-badge {
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.65rem;
            border-radius: var(--radius-full);
            background: var(--color-accent-subtle);
            color: var(--color-success);
            border: 1px solid rgba(143, 175, 155, 0.22);
            font-size: 0.76rem;
            font-weight: 650;
            white-space: nowrap;
        }

        .roi-results-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.85rem;
            margin-top: 1rem;
        }

        .roi-result {
            padding: 1rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--color-border);
            background: var(--color-bg-soft);
        }

        .roi-result-label {
            color: var(--color-text-secondary);
            font-size: 0.8rem;
            margin-bottom: 0.3rem;
        }

        .roi-result-value {
            color: var(--color-text-primary);
            font-size: 1.35rem;
            font-weight: 650;
            letter-spacing: -0.03em;
        }

        .roi-result-value.highlight {
            color: var(--color-primary);
        }

        .why-disclaimer {
            margin-top: 0.9rem;
            padding: 0.85rem 1rem;
            border-radius: var(--radius-md);
            background: var(--color-primary-subtle);
            border: 1px solid rgba(61, 58, 140, 0.14);
            color: var(--color-text-secondary);
            font-size: 0.84rem;
            line-height: 1.55;
        }

        @media (max-width: 980px) {
            .why-hero-grid,
            .cost-leak-grid,
            .roi-results-grid {
                grid-template-columns: 1fr;
            }
        }


        /* -----------------------------
           SupportOps Page Polish
        ----------------------------- */
        .support-intro-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.04fr) minmax(320px, 0.96fr);
            gap: 1rem;
            margin-bottom: 1rem;
            animation: fadeUp 0.65s ease-out;
        }

        .support-workflow-card,
        .support-status-card,
        .support-empty-card,
        .support-report-card {
            padding: 1.25rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
        }

        .support-workflow-title,
        .support-status-title,
        .support-report-title {
            color: var(--color-text-primary);
            font-size: 1.1rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            margin-bottom: 0.4rem;
        }

        .support-workflow-copy,
        .support-status-copy,
        .support-empty-copy,
        .support-report-copy {
            color: var(--color-text-secondary);
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .support-step-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
            margin-top: 1rem;
        }

        .support-step {
            padding: 0.75rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--color-border);
            background: var(--color-bg-soft);
        }

        .support-step-num {
            display: inline-grid;
            place-items: center;
            width: 24px;
            height: 24px;
            border-radius: 999px;
            background: var(--color-primary-subtle);
            color: var(--color-primary);
            font-size: 0.72rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
        }

        .support-step-title {
            color: var(--color-text-primary);
            font-size: 0.82rem;
            font-weight: 650;
            margin-bottom: 0.15rem;
        }

        .support-step-copy {
            color: var(--color-text-secondary);
            font-size: 0.74rem;
            line-height: 1.42;
        }

        .support-control-panel {
            margin: 1rem 0;
            padding: 1rem;
            border-radius: var(--radius-lg);
            border: 1px solid var(--color-border);
            background:
                linear-gradient(135deg, rgba(61, 58, 140, 0.045), rgba(143, 175, 155, 0.055)),
                #ffffff;
            box-shadow: var(--shadow-xs);
        }

        .support-control-heading {
            color: var(--color-text-primary);
            font-size: 0.95rem;
            font-weight: 650;
            margin-bottom: 0.2rem;
        }

        .support-control-copy {
            color: var(--color-text-secondary);
            font-size: 0.82rem;
            line-height: 1.5;
            margin-bottom: 0.8rem;
        }

        .support-empty-card {
            margin-top: 1rem;
            text-align: left;
            background:
                radial-gradient(circle at 90% 10%, rgba(61, 58, 140, 0.08), transparent 30%),
                #ffffff;
        }

        .support-empty-title {
            color: var(--color-text-primary);
            font-size: 1.25rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            margin-bottom: 0.35rem;
        }

        .support-empty-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.9rem;
        }

        .support-mini-badge {
            display: inline-flex;
            padding: 0.38rem 0.62rem;
            border-radius: var(--radius-full);
            background: var(--color-primary-subtle);
            color: var(--color-primary);
            border: 1px solid rgba(61, 58, 140, 0.14);
            font-size: 0.76rem;
            font-weight: 600;
        }

        .support-data-banner {
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 1rem;
            align-items: center;
            margin: 1rem 0;
            padding: 1rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        .support-data-title {
            color: var(--color-text-primary);
            font-weight: 650;
            margin-bottom: 0.15rem;
        }

        .support-data-sub {
            color: var(--color-text-secondary);
            font-size: 0.82rem;
        }

        .support-data-pill {
            padding: 0.42rem 0.65rem;
            border-radius: var(--radius-full);
            background: var(--color-bg-soft);
            color: var(--color-text-secondary);
            border: 1px solid var(--color-border);
            font-size: 0.78rem;
            font-weight: 600;
            white-space: nowrap;
        }

        .support-tab-note {
            margin: 0.3rem 0 1rem 0;
            padding: 0.85rem 1rem;
            border-radius: var(--radius-md);
            border: 1px solid rgba(61, 58, 140, 0.14);
            background: var(--color-primary-subtle);
            color: var(--color-text-secondary);
            font-size: 0.84rem;
            line-height: 1.52;
        }

        .support-agent-result {
            margin-top: 1rem;
            padding: 1.15rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
        }

        .support-agent-title {
            color: var(--color-text-primary);
            font-size: 1rem;
            font-weight: 650;
            margin-bottom: 0.4rem;
        }

        .support-agent-box {
            padding: 0.9rem;
            border-radius: var(--radius-md);
            background: var(--color-bg-soft);
            border: 1px solid var(--color-border);
            color: var(--color-text-secondary);
            line-height: 1.55;
            margin-top: 0.55rem;
        }

        .support-report-card {
            margin-bottom: 1rem;
        }

        @media (max-width: 980px) {
            .support-intro-grid,
            .support-step-grid,
            .support-data-banner {
                grid-template-columns: 1fr;
            }
        }


        /* -----------------------------
           CostOps Page Polish
        ----------------------------- */
        .costops-intro-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.04fr) minmax(320px, 0.96fr);
            gap: 1rem;
            margin-bottom: 1rem;
            animation: fadeUp 0.65s ease-out;
        }

        .costops-story-card,
        .costops-signal-card,
        .costops-control-panel,
        .costops-report-card {
            padding: 1.25rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
        }

        .costops-story-card {
            background:
                radial-gradient(circle at 88% 18%, rgba(154, 116, 53, 0.08), transparent 30%),
                linear-gradient(135deg, #ffffff, #fafaf9);
        }

        .costops-title {
            color: var(--color-text-primary);
            font-size: 1.18rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            margin-bottom: 0.4rem;
        }

        .costops-copy {
            color: var(--color-text-secondary);
            font-size: 0.9rem;
            line-height: 1.58;
        }

        .costops-signal-list {
            display: grid;
            gap: 0.65rem;
            margin-top: 0.9rem;
        }

        .costops-signal-row {
            display: grid;
            grid-template-columns: 34px 1fr;
            gap: 0.75rem;
            align-items: start;
            padding: 0.7rem;
            border-radius: var(--radius-md);
            background: var(--color-bg-soft);
            border: 1px solid var(--color-border);
        }

        .costops-signal-icon {
            width: 34px;
            height: 34px;
            border-radius: 11px;
            display: grid;
            place-items: center;
            background: var(--color-warning-bg);
            color: var(--color-warning);
            font-weight: 650;
        }

        .costops-signal-row b {
            color: var(--color-text-primary);
            font-weight: 650;
        }

        .costops-signal-row p {
            color: var(--color-text-secondary);
            margin: 0.15rem 0 0 0;
            font-size: 0.82rem;
            line-height: 1.42;
        }

        .costops-control-panel {
            margin: 1rem 0;
            background:
                linear-gradient(135deg, rgba(154, 116, 53, 0.055), rgba(143, 175, 155, 0.055)),
                #ffffff;
        }

        .costops-control-heading {
            color: var(--color-text-primary);
            font-size: 0.95rem;
            font-weight: 650;
            margin-bottom: 0.2rem;
        }

        .costops-control-copy {
            color: var(--color-text-secondary);
            font-size: 0.82rem;
            line-height: 1.5;
        }

        .costops-data-banner {
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 1rem;
            align-items: center;
            margin: 1rem 0;
            padding: 1rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        .costops-data-title {
            color: var(--color-text-primary);
            font-weight: 650;
            margin-bottom: 0.15rem;
        }

        .costops-data-sub {
            color: var(--color-text-secondary);
            font-size: 0.82rem;
        }

        .costops-data-pill {
            padding: 0.42rem 0.65rem;
            border-radius: var(--radius-full);
            background: var(--color-warning-bg);
            color: var(--color-warning);
            border: 1px solid rgba(154, 116, 53, 0.18);
            font-size: 0.78rem;
            font-weight: 650;
            white-space: nowrap;
        }

        .costops-tab-note {
            margin: 0.3rem 0 1rem 0;
            padding: 0.85rem 1rem;
            border-radius: var(--radius-md);
            border: 1px solid rgba(154, 116, 53, 0.18);
            background: var(--color-warning-bg);
            color: var(--color-text-secondary);
            font-size: 0.84rem;
            line-height: 1.52;
        }

        .costops-savings-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.85rem;
            margin: 1rem 0;
        }

        .costops-savings-card {
            padding: 1rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--color-border);
            background: #ffffff;
            box-shadow: var(--shadow-xs);
        }

        .costops-savings-label {
            color: var(--color-text-secondary);
            font-size: 0.8rem;
            margin-bottom: 0.3rem;
        }

        .costops-savings-value {
            color: var(--color-text-primary);
            font-size: 1.3rem;
            font-weight: 650;
            letter-spacing: -0.03em;
        }

        .costops-savings-value.highlight {
            color: var(--color-warning);
        }

        .costops-report-card {
            margin-bottom: 1rem;
        }

        @media (max-width: 980px) {
            .costops-intro-grid,
            .costops-data-banner,
            .costops-savings-grid {
                grid-template-columns: 1fr;
            }
        }


        /* -----------------------------
           NextHire AI Page Polish
        ----------------------------- */
        .nexthire-intro-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.04fr) minmax(320px, 0.96fr);
            gap: 1rem;
            margin-bottom: 1rem;
            animation: fadeUp 0.65s ease-out;
        }

        .nexthire-story-card,
        .nexthire-signal-card,
        .nexthire-control-panel,
        .nexthire-report-card,
        .nexthire-ai-panel {
            padding: 1.25rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
        }

        .nexthire-story-card {
            background:
                radial-gradient(circle at 88% 18%, rgba(61, 58, 140, 0.08), transparent 30%),
                linear-gradient(135deg, #ffffff, #fafaf9);
        }

        .nexthire-title {
            color: var(--color-text-primary);
            font-size: 1.18rem;
            font-weight: 650;
            letter-spacing: -0.02em;
            margin-bottom: 0.4rem;
        }

        .nexthire-copy {
            color: var(--color-text-secondary);
            font-size: 0.9rem;
            line-height: 1.58;
        }

        .nexthire-signal-list {
            display: grid;
            gap: 0.65rem;
            margin-top: 0.9rem;
        }

        .nexthire-signal-row {
            display: grid;
            grid-template-columns: 34px 1fr;
            gap: 0.75rem;
            align-items: start;
            padding: 0.7rem;
            border-radius: var(--radius-md);
            background: var(--color-bg-soft);
            border: 1px solid var(--color-border);
        }

        .nexthire-signal-icon {
            width: 34px;
            height: 34px;
            border-radius: 11px;
            display: grid;
            place-items: center;
            background: var(--color-primary-subtle);
            color: var(--color-primary);
            font-weight: 650;
        }

        .nexthire-signal-row b {
            color: var(--color-text-primary);
            font-weight: 650;
        }

        .nexthire-signal-row p {
            color: var(--color-text-secondary);
            margin: 0.15rem 0 0 0;
            font-size: 0.82rem;
            line-height: 1.42;
        }

        .nexthire-control-panel {
            margin: 1rem 0;
            background:
                linear-gradient(135deg, rgba(61, 58, 140, 0.045), rgba(143, 175, 155, 0.055)),
                #ffffff;
        }

        .nexthire-control-heading {
            color: var(--color-text-primary);
            font-size: 0.95rem;
            font-weight: 650;
            margin-bottom: 0.2rem;
        }

        .nexthire-control-copy {
            color: var(--color-text-secondary);
            font-size: 0.82rem;
            line-height: 1.5;
        }

        .nexthire-score-strip {
            display: grid;
            grid-template-columns: 1.1fr repeat(3, 0.8fr);
            gap: 0.85rem;
            margin: 1rem 0;
        }

        .nexthire-score-card {
            padding: 1rem;
            border-radius: var(--radius-md);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        .nexthire-score-card.primary {
            background:
                radial-gradient(circle at 85% 12%, rgba(61, 58, 140, 0.10), transparent 36%),
                #ffffff;
            border-color: rgba(61, 58, 140, 0.18);
        }

        .nexthire-score-label {
            color: var(--color-text-secondary);
            font-size: 0.78rem;
            margin-bottom: 0.3rem;
        }

        .nexthire-score-value {
            color: var(--color-text-primary);
            font-size: 1.35rem;
            font-weight: 650;
            letter-spacing: -0.03em;
        }

        .nexthire-score-value.highlight {
            color: var(--color-primary);
            font-size: 1.75rem;
        }

        .nexthire-tab-note {
            margin: 0.3rem 0 1rem 0;
            padding: 0.85rem 1rem;
            border-radius: var(--radius-md);
            border: 1px solid rgba(61, 58, 140, 0.14);
            background: var(--color-primary-subtle);
            color: var(--color-text-secondary);
            font-size: 0.84rem;
            line-height: 1.52;
        }

        .nexthire-keyword-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .nexthire-keyword-card {
            padding: 1rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        .nexthire-keyword-title {
            color: var(--color-text-primary);
            font-weight: 650;
            margin-bottom: 0.5rem;
        }

        .keyword-pill-wrap {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
        }

        .keyword-pill {
            display: inline-flex;
            padding: 0.34rem 0.55rem;
            border-radius: var(--radius-full);
            font-size: 0.74rem;
            font-weight: 600;
            border: 1px solid var(--color-border);
            background: var(--color-bg-soft);
            color: var(--color-text-secondary);
        }

        .keyword-pill.good {
            background: var(--color-success-bg);
            color: var(--color-success);
            border-color: rgba(85, 124, 95, 0.18);
        }

        .keyword-pill.gap {
            background: var(--color-danger-bg);
            color: var(--color-danger);
            border-color: rgba(155, 74, 74, 0.18);
        }

        .nexthire-ai-panel {
            margin-bottom: 1rem;
            background:
                linear-gradient(135deg, rgba(61, 58, 140, 0.045), rgba(143, 175, 155, 0.050)),
                #ffffff;
        }

        .nexthire-ai-status {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.38rem 0.65rem;
            border-radius: var(--radius-full);
            background: var(--color-accent-subtle);
            color: var(--color-success);
            border: 1px solid rgba(143, 175, 155, 0.22);
            font-size: 0.76rem;
            font-weight: 650;
            margin-bottom: 0.65rem;
        }

        .nexthire-list-card {
            padding: 1rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--color-border);
            background: #ffffff;
            margin-bottom: 0.8rem;
        }

        .nexthire-list-title {
            color: var(--color-text-primary);
            font-weight: 650;
            margin-bottom: 0.45rem;
        }

        .nexthire-report-card {
            margin-bottom: 1rem;
        }

        @media (max-width: 980px) {
            .nexthire-intro-grid,
            .nexthire-score-strip,
            .nexthire-keyword-grid {
                grid-template-columns: 1fr;
            }
        }

        /* -----------------------------
           Footer
        ----------------------------- */
        .ops-footer {
            margin-top: 2.35rem;
            padding: 1.65rem 0 1.2rem 0;
            border-top: 1px solid var(--color-border);
            color: var(--color-text-secondary);
            font-size: 0.86rem;
        }

        .footer-grid {
            display: grid;
            grid-template-columns: 1.35fr 1fr 1fr 1fr;
            gap: 1.2rem;
        }

        .ops-footer b {
            color: var(--color-text-primary);
            font-weight: 600;
        }

        .footer-brand {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            margin-bottom: 0.45rem;
        }

        .footer-mini-logo {
            width: 28px;
            height: 28px;
            border-radius: 9px;
            background: linear-gradient(135deg, #3d3a8c, #8faf9b);
        }

        .footer-line {
            margin-top: 1.15rem;
            color: var(--color-text-tertiary);
            font-size: 0.78rem;
            text-align: center;
        }

        @media (max-width: 980px) {
            .hero-panel,
            .dashboard-preview-card {
                min-height: auto;
            }

            .mock-kpis {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .mock-lower,
            .impact-grid {
                grid-template-columns: 1fr;
            }

            .mock-layout {
                grid-template-columns: 1fr;
            }

            .mock-sidebar {
                display: none;
            }

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

        /* -----------------------------
           Step 6: Global Animation Polish
           Professional, subtle motion across the whole application.
        ----------------------------- */
        @keyframes pageFadeUp {
            from {
                opacity: 0;
                transform: translateY(14px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes cardSoftIn {
            from {
                opacity: 0;
                transform: translateY(12px) scale(0.992);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        @keyframes previewFloat {
            0% {
                transform: translateY(0);
                box-shadow: var(--shadow-lg);
            }
            50% {
                transform: translateY(-6px);
                box-shadow: 0 30px 70px rgba(28, 28, 26, 0.12);
            }
            100% {
                transform: translateY(0);
                box-shadow: var(--shadow-lg);
            }
        }

        @keyframes accentLineGrow {
            from {
                width: 0;
                opacity: 0;
            }
            to {
                width: 76px;
                opacity: 1;
            }
        }

        @keyframes quietPulse {
            0% {
                box-shadow: 0 0 0 0 rgba(143, 175, 155, 0.22);
            }
            70% {
                box-shadow: 0 0 0 8px rgba(143, 175, 155, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(143, 175, 155, 0);
            }
        }

        @keyframes shimmerSoft {
            0% {
                background-position: -160px 0;
            }
            100% {
                background-position: 160px 0;
            }
        }

        .block-container {
            animation: pageFadeUp 420ms ease-out both;
        }

        .hero-panel,
        .dashboard-preview-card,
        .module-header,
        .why-hero-panel,
        .why-proof-card,
        .support-workflow-card,
        .support-status-card,
        .costops-story-card,
        .costops-signal-card,
        .nexthire-story-card,
        .nexthire-signal-card {
            animation: cardSoftIn 520ms ease-out both;
        }

        .dashboard-preview-card {
            animation:
                cardSoftIn 520ms ease-out both,
                previewFloat 7s ease-in-out 900ms infinite;
        }

        .app-card,
        .value-card,
        .metric-card,
        .support-step,
        .support-control-panel,
        .support-empty-card,
        .support-data-banner,
        .support-agent-result,
        .support-report-card,
        .costops-control-panel,
        .costops-data-banner,
        .costops-savings-card,
        .costops-report-card,
        .nexthire-control-panel,
        .nexthire-ai-panel,
        .nexthire-score-card,
        .nexthire-keyword-card,
        .nexthire-list-card,
        .nexthire-report-card,
        [data-testid="stMetric"] {
            animation: cardSoftIn 480ms ease-out both;
            transition:
                transform var(--transition-medium),
                border-color var(--transition-medium),
                box-shadow var(--transition-medium),
                background-color var(--transition-medium),
                color var(--transition-fast);
        }

        .app-card:hover,
        .value-card:hover,
        .metric-card:hover,
        .support-step:hover,
        .support-control-panel:hover,
        .support-data-banner:hover,
        .support-agent-result:hover,
        .support-report-card:hover,
        .costops-control-panel:hover,
        .costops-data-banner:hover,
        .costops-savings-card:hover,
        .costops-report-card:hover,
        .nexthire-control-panel:hover,
        .nexthire-ai-panel:hover,
        .nexthire-score-card:hover,
        .nexthire-keyword-card:hover,
        .nexthire-list-card:hover,
        .nexthire-report-card:hover,
        [data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            border-color: var(--color-border-hover);
            box-shadow: var(--shadow-md);
        }

        .section-title::after {
            content: "";
            display: block;
            height: 3px;
            width: 76px;
            margin: 0.75rem auto 0 auto;
            border-radius: var(--radius-full);
            background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
            animation: accentLineGrow 520ms ease-out both;
        }

        .module-title::after,
        .support-workflow-title::after,
        .costops-title::after,
        .nexthire-title::after,
        .why-title::after,
        .roi-panel-title::after {
            content: "";
            display: block;
            height: 2px;
            width: 54px;
            margin-top: 0.55rem;
            border-radius: var(--radius-full);
            background: linear-gradient(90deg, var(--color-primary), var(--color-accent));
            animation: accentLineGrow 520ms ease-out both;
        }

        .nav-note-dot,
        .nexthire-ai-status::before {
            animation: quietPulse 2.4s ease-in-out infinite;
        }

        .nexthire-ai-status::before {
            content: "";
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: var(--color-accent);
            display: inline-block;
        }

        .support-data-pill,
        .costops-data-pill,
        .support-mini-badge,
        .keyword-pill,
        .tech-pill,
        .proof-pill,
        .roi-badge,
        .nexthire-ai-status {
            transition:
                transform var(--transition-fast),
                border-color var(--transition-fast),
                background-color var(--transition-fast),
                color var(--transition-fast);
        }

        .support-data-pill:hover,
        .costops-data-pill:hover,
        .support-mini-badge:hover,
        .keyword-pill:hover,
        .tech-pill:hover,
        .proof-pill:hover,
        .roi-badge:hover,
        .nexthire-ai-status:hover {
            transform: translateY(-1px);
            border-color: var(--color-border-hover);
        }

        .mock-kpi,
        .mock-chart-card,
        .mock-activity-card,
        .mock-activity-row {
            transition:
                transform var(--transition-medium),
                border-color var(--transition-medium),
                background-color var(--transition-medium);
        }

        .mock-kpi:hover,
        .mock-chart-card:hover,
        .mock-activity-card:hover {
            transform: translateY(-2px);
            border-color: var(--color-border-hover);
        }

        .mock-link,
        .value-list,
        .cost-row-value,
        .nexthire-score-value.highlight,
        .costops-savings-value.highlight {
            background-image: linear-gradient(
                90deg,
                var(--color-primary),
                var(--color-accent),
                var(--color-primary)
            );
            background-size: 220% 100%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmerSoft 7s linear infinite;
        }

        div.stButton > button {
            position: relative;
            overflow: hidden;
        }

        div.stButton > button::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(
                120deg,
                transparent 0%,
                rgba(61, 58, 140, 0.08) 45%,
                transparent 70%
            );
            transform: translateX(-120%);
            transition: transform 420ms ease;
        }

        div.stButton > button:hover::after {
            transform: translateX(120%);
        }

        .stTabs [data-baseweb="tab"] {
            transition:
                background-color var(--transition-fast),
                border-color var(--transition-fast),
                color var(--transition-fast),
                transform var(--transition-fast);
        }

        .stTabs [data-baseweb="tab"]:hover {
            transform: translateY(-1px);
            border-color: var(--color-primary);
            background: var(--color-primary-subtle);
            color: var(--color-primary);
        }

        .stTextArea textarea:focus,
        .stTextInput input:focus,
        .stNumberInput input:focus {
            border-color: var(--color-primary);
            box-shadow: none;
        }

        /* Staggered entrance effect for common card rows */
        div[data-testid="column"]:nth-child(1) .app-card,
        div[data-testid="column"]:nth-child(1) .value-card,
        div[data-testid="column"]:nth-child(1) [data-testid="stMetric"],
        div[data-testid="column"]:nth-child(1) .costops-savings-card,
        div[data-testid="column"]:nth-child(1) .nexthire-score-card {
            animation-delay: 40ms;
        }

        div[data-testid="column"]:nth-child(2) .app-card,
        div[data-testid="column"]:nth-child(2) .value-card,
        div[data-testid="column"]:nth-child(2) [data-testid="stMetric"],
        div[data-testid="column"]:nth-child(2) .costops-savings-card,
        div[data-testid="column"]:nth-child(2) .nexthire-score-card {
            animation-delay: 100ms;
        }

        div[data-testid="column"]:nth-child(3) .app-card,
        div[data-testid="column"]:nth-child(3) .value-card,
        div[data-testid="column"]:nth-child(3) [data-testid="stMetric"],
        div[data-testid="column"]:nth-child(3) .costops-savings-card,
        div[data-testid="column"]:nth-child(3) .nexthire-score-card {
            animation-delay: 160ms;
        }

        div[data-testid="column"]:nth-child(4) [data-testid="stMetric"],
        div[data-testid="column"]:nth-child(4) .nexthire-score-card {
            animation-delay: 220ms;
        }

        /* Keep motion accessible */
        @media (prefers-reduced-motion: reduce) {
            *,
            *::before,
            *::after {
                animation-duration: 0.001ms;
                animation-iteration-count: 1;
                scroll-behavior: auto;
                transition-duration: 0.001ms;
            }

            .dashboard-preview-card {
                animation: none;
            }
        }


        /* -----------------------------
           Step 7: Final Product Polish
           Make Streamlit controls feel closer to a real SaaS product.
        ----------------------------- */

        .main .block-container {
            max-width: 1240px;
            padding-top: 1.25rem;
            padding-bottom: 2.5rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.025em;
        }

        h2, h3 {
            color: var(--color-text-primary);
        }

        p, li {
            color: var(--color-text-secondary);
        }

        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            padding: 0.95rem 1rem;
            box-shadow: var(--shadow-xs);
        }

        [data-testid="stMetricLabel"] {
            color: var(--color-text-muted);
            font-size: 0.78rem;
        }

        [data-testid="stMetricValue"] {
            color: var(--color-text-primary);
            font-weight: 650;
            letter-spacing: -0.035em;
        }

        [data-testid="stMetricDelta"] {
            color: var(--color-success);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.45rem;
            border-bottom: 1px solid var(--color-border);
            padding-bottom: 0.45rem;
            margin-bottom: 1rem;
        }

        .stTabs [data-baseweb="tab"] {
            height: 40px;
            border-radius: var(--radius-full);
            padding: 0 1rem;
            background: #ffffff;
            border: 1px solid var(--color-border);
            color: var(--color-text-secondary);
            font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
            background: var(--color-primary-subtle);
            border-color: rgba(61, 58, 140, 0.22);
            color: var(--color-primary);
        }

        .stTabs [data-baseweb="tab-highlight"] {
            display: none;
        }

        [data-testid="stFileUploader"] {
            padding: 0.35rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        [data-testid="stFileUploaderDropzone"] {
            border: 1.5px dashed rgba(61, 58, 140, 0.22);
            border-radius: var(--radius-md);
            background:
                linear-gradient(135deg, rgba(61, 58, 140, 0.035), rgba(143, 175, 155, 0.045)),
                #ffffff;
            transition:
                border-color var(--transition-medium),
                background-color var(--transition-medium),
                transform var(--transition-medium);
        }

        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: rgba(61, 58, 140, 0.42);
            transform: translateY(-2px);
        }

        [data-testid="stFileUploaderDropzone"] button {
            border-radius: var(--radius-full);
        }

        .stTextArea textarea,
        .stTextInput input,
        .stNumberInput input {
            border-radius: var(--radius-md);
            border: 1px solid var(--color-border);
            background: #ffffff;
            color: var(--color-text-primary);
        }

        .stTextArea textarea {
            line-height: 1.55;
        }

        .stTextArea textarea:hover,
        .stTextInput input:hover,
        .stNumberInput input:hover {
            border-color: var(--color-border-hover);
        }

        label[data-testid="stWidgetLabel"] p {
            color: var(--color-text-primary);
            font-weight: 650;
            font-size: 0.86rem;
        }

        [data-testid="stSlider"] {
            padding: 0.65rem 0.75rem;
            border-radius: var(--radius-md);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        [data-baseweb="select"] > div {
            border-radius: var(--radius-md);
            border-color: var(--color-border);
            background: #ffffff;
        }

        [data-baseweb="select"] > div:hover {
            border-color: var(--color-border-hover);
        }

        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            border-radius: var(--radius-lg);
            border: 1px solid var(--color-border);
            overflow: hidden;
            box-shadow: var(--shadow-xs);
            background: #ffffff;
        }

        .stCodeBlock {
            border-radius: var(--radius-md);
            border: 1px solid var(--color-border);
            overflow: hidden;
        }

        [data-testid="stDownloadButton"] button {
            border-radius: var(--radius-full);
            font-weight: 650;
        }

        [data-testid="stAlert"] {
            border-radius: var(--radius-md);
            border: 1px solid var(--color-border);
        }

        [data-testid="stPlotlyChart"] {
            padding: 0.65rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
            margin-bottom: 1rem;
            animation: cardSoftIn 480ms ease-out both;
            transition:
                transform var(--transition-medium),
                border-color var(--transition-medium),
                box-shadow var(--transition-medium);
        }

        [data-testid="stPlotlyChart"]:hover {
            transform: translateY(-2px);
            border-color: var(--color-border-hover);
            box-shadow: var(--shadow-md);
        }

        div[data-testid="stVerticalBlock"] > div:has(.section-title),
        div[data-testid="stVerticalBlock"] > div:has(.module-header) {
            margin-top: 0.25rem;
        }

        .costops-signal-card .costops-title::after,
        .nexthire-signal-card .nexthire-title::after,
        .support-status-card .support-status-title::after {
            display: none;
        }

        textarea[aria-label="Report Preview"],
        textarea[aria-label="CostOps Report Preview"],
        textarea[aria-label="Hiring Report Preview"] {
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 0.84rem;
            background: #fbfbfa;
        }

        .footer-shell {
            margin-top: 3rem;
        }


        /* -----------------------------
           Step 8: Brighter SaaS Motion Upgrade
           More lively color + premium motion, still professional.
        ----------------------------- */

        :root {
            --color-primary: #4f46e5;
            --color-primary-hover: #4338ca;
            --color-primary-subtle: #eef2ff;
            --color-accent: #10b981;
            --color-accent-subtle: #ecfdf5;
            --color-success: #059669;
            --color-success-bg: #ecfdf5;
            --color-warning: #f59e0b;
            --color-warning-bg: #fffbeb;
            --color-danger: #ef4444;
            --color-danger-bg: #fef2f2;
            --color-bg: #fbfcff;
            --color-bg-soft: #f8fafc;
            --color-border: #e5e7eb;
            --color-border-hover: #c7d2fe;
            --shadow-xs: 0 4px 14px rgba(15, 23, 42, 0.045);
            --shadow-sm: 0 10px 26px rgba(15, 23, 42, 0.07);
            --shadow-md: 0 18px 44px rgba(15, 23, 42, 0.10);
            --shadow-lg: 0 28px 80px rgba(79, 70, 229, 0.16);
        }

        @keyframes gradientDrift {
            0% {
                background-position: 0% 50%;
            }
            50% {
                background-position: 100% 50%;
            }
            100% {
                background-position: 0% 50%;
            }
        }

        @keyframes strongerFloat {
            0% {
                transform: translateY(0) rotate(0deg);
            }
            50% {
                transform: translateY(-8px) rotate(-0.35deg);
            }
            100% {
                transform: translateY(0) rotate(0deg);
            }
        }

        @keyframes metricPop {
            0% {
                opacity: 0;
                transform: translateY(10px) scale(0.96);
            }
            60% {
                opacity: 1;
                transform: translateY(-2px) scale(1.015);
            }
            100% {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        @keyframes borderGlow {
            0% {
                opacity: 0.35;
                transform: translateX(-120%);
            }
            50% {
                opacity: 0.85;
            }
            100% {
                opacity: 0.35;
                transform: translateX(120%);
            }
        }

        @keyframes softColorPulse {
            0%, 100% {
                filter: saturate(1);
            }
            50% {
                filter: saturate(1.25);
            }
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 8%, rgba(79, 70, 229, 0.10), transparent 32%),
                radial-gradient(circle at 92% 14%, rgba(16, 185, 129, 0.10), transparent 30%),
                radial-gradient(circle at 52% 88%, rgba(245, 158, 11, 0.06), transparent 34%),
                linear-gradient(135deg, #fbfcff 0%, #f8fafc 45%, #ffffff 100%);
            background-size: 180% 180%;
            animation: gradientDrift 18s ease infinite;
        }

        .topbar {
            background:
                linear-gradient(135deg, rgba(255,255,255,0.92), rgba(255,255,255,0.78)),
                linear-gradient(90deg, rgba(79,70,229,0.06), rgba(16,185,129,0.06));
            backdrop-filter: blur(20px);
            border-color: rgba(199, 210, 254, 0.62);
            box-shadow: 0 14px 36px rgba(15, 23, 42, 0.07);
        }

        .brand-mark,
        .mock-avatar,
        .value-icon,
        .support-step-num,
        .why-proof-icon,
        .nexthire-signal-icon {
            background: linear-gradient(135deg, var(--color-primary), #7c3aed);
            color: #ffffff;
            box-shadow: 0 10px 22px rgba(79, 70, 229, 0.20);
        }

        .hero-panel,
        .why-hero-panel,
        .module-header,
        .support-workflow-card,
        .costops-story-card,
        .nexthire-story-card {
            background:
                radial-gradient(circle at 85% 12%, rgba(79, 70, 229, 0.14), transparent 28%),
                radial-gradient(circle at 12% 88%, rgba(16, 185, 129, 0.10), transparent 32%),
                linear-gradient(135deg, #ffffff, #f8fafc);
            border-color: rgba(199, 210, 254, 0.78);
        }

        .hero-title span,
        .why-title span,
        .module-title,
        .nexthire-score-value.highlight,
        .costops-savings-value.highlight {
            background-image: linear-gradient(90deg, #4f46e5, #7c3aed, #10b981);
            background-size: 220% 100%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmerSoft 6s linear infinite;
        }

        .dashboard-preview-card {
            border-color: rgba(199, 210, 254, 0.82);
            box-shadow: 0 26px 70px rgba(79, 70, 229, 0.16);
            animation:
                cardSoftIn 520ms ease-out both,
                strongerFloat 6.5s ease-in-out 900ms infinite;
        }

        .app-card,
        .value-card,
        .metric-card,
        .why-proof-card,
        .support-status-card,
        .support-control-panel,
        .support-empty-card,
        .support-data-banner,
        .support-agent-result,
        .support-report-card,
        .costops-signal-card,
        .costops-control-panel,
        .costops-data-banner,
        .costops-savings-card,
        .costops-report-card,
        .nexthire-signal-card,
        .nexthire-control-panel,
        .nexthire-ai-panel,
        .nexthire-score-card,
        .nexthire-keyword-card,
        .nexthire-list-card,
        .nexthire-report-card,
        [data-testid="stMetric"],
        [data-testid="stPlotlyChart"] {
            position: relative;
            overflow: hidden;
            border-color: rgba(226, 232, 240, 0.96);
        }

        .app-card::before,
        .value-card::before,
        .metric-card::before,
        .why-proof-card::before,
        .support-status-card::before,
        .support-control-panel::before,
        .support-data-banner::before,
        .costops-signal-card::before,
        .costops-control-panel::before,
        .costops-data-banner::before,
        .nexthire-signal-card::before,
        .nexthire-control-panel::before,
        .nexthire-ai-panel::before,
        .nexthire-score-card::before,
        [data-testid="stMetric"]::before,
        [data-testid="stPlotlyChart"]::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            height: 2px;
            width: 100%;
            background: linear-gradient(90deg, transparent, #4f46e5, #10b981, transparent);
            transform: translateX(-120%);
            opacity: 0;
            pointer-events: none;
        }

        .app-card:hover::before,
        .value-card:hover::before,
        .metric-card:hover::before,
        .why-proof-card:hover::before,
        .support-status-card:hover::before,
        .support-control-panel:hover::before,
        .support-data-banner:hover::before,
        .costops-signal-card:hover::before,
        .costops-control-panel:hover::before,
        .costops-data-banner:hover::before,
        .nexthire-signal-card:hover::before,
        .nexthire-control-panel:hover::before,
        .nexthire-ai-panel:hover::before,
        .nexthire-score-card:hover::before,
        [data-testid="stMetric"]:hover::before,
        [data-testid="stPlotlyChart"]:hover::before {
            opacity: 1;
            animation: borderGlow 1.4s ease;
        }

        .app-card:hover,
        .value-card:hover,
        .metric-card:hover,
        .why-proof-card:hover,
        .support-status-card:hover,
        .support-control-panel:hover,
        .support-data-banner:hover,
        .costops-signal-card:hover,
        .costops-control-panel:hover,
        .costops-data-banner:hover,
        .nexthire-signal-card:hover,
        .nexthire-control-panel:hover,
        .nexthire-ai-panel:hover,
        .nexthire-score-card:hover,
        [data-testid="stMetric"]:hover,
        [data-testid="stPlotlyChart"]:hover {
            transform: translateY(-5px);
            border-color: rgba(129, 140, 248, 0.72);
            box-shadow: 0 22px 54px rgba(79, 70, 229, 0.13);
        }

        [data-testid="stMetric"] {
            animation: metricPop 520ms ease-out both;
            background:
                radial-gradient(circle at 92% 15%, rgba(79, 70, 229, 0.055), transparent 36%),
                #ffffff;
        }

        [data-testid="stMetricValue"] {
            color: var(--color-primary);
        }

        div.stButton > button,
        [data-testid="stDownloadButton"] button {
            background: linear-gradient(135deg, var(--color-primary), #7c3aed);
            border: 1px solid rgba(79, 70, 229, 0.28);
            color: #ffffff;
            box-shadow: 0 12px 28px rgba(79, 70, 229, 0.18);
        }

        div.stButton > button:hover,
        [data-testid="stDownloadButton"] button:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 40px rgba(79, 70, 229, 0.24);
            border-color: rgba(124, 58, 237, 0.42);
        }

        div.stButton > button:active,
        [data-testid="stDownloadButton"] button:active {
            transform: translateY(0) scale(0.985);
        }

        .tech-pill,
        .proof-pill,
        .support-mini-badge,
        .keyword-pill,
        .roi-badge,
        .nexthire-ai-status,
        .support-data-pill,
        .costops-data-pill {
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.045);
            animation: softColorPulse 5s ease-in-out infinite;
        }

        .tech-pill:hover,
        .proof-pill:hover,
        .support-mini-badge:hover,
        .keyword-pill:hover,
        .roi-badge:hover,
        .nexthire-ai-status:hover,
        .support-data-pill:hover,
        .costops-data-pill:hover {
            transform: translateY(-2px) scale(1.02);
            box-shadow: 0 12px 24px rgba(79, 70, 229, 0.12);
        }

        .section-title::after,
        .module-title::after,
        .support-workflow-title::after,
        .costops-title::after,
        .nexthire-title::after,
        .why-title::after,
        .roi-panel-title::after {
            background: linear-gradient(90deg, #4f46e5, #7c3aed, #10b981);
            box-shadow: 0 0 18px rgba(79, 70, 229, 0.18);
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #eef2ff, #ecfdf5);
            border-color: rgba(129, 140, 248, 0.55);
            color: var(--color-primary);
            box-shadow: 0 10px 22px rgba(79, 70, 229, 0.08);
        }

        [data-testid="stPlotlyChart"] {
            background:
                radial-gradient(circle at 95% 10%, rgba(79, 70, 229, 0.045), transparent 34%),
                #ffffff;
        }

        [data-testid="stFileUploaderDropzone"] {
            background:
                radial-gradient(circle at 95% 10%, rgba(79, 70, 229, 0.08), transparent 32%),
                linear-gradient(135deg, #ffffff, #f8fafc);
            border-color: rgba(129, 140, 248, 0.45);
        }

        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: rgba(79, 70, 229, 0.75);
            box-shadow: 0 14px 30px rgba(79, 70, 229, 0.10);
        }

        /* Keep it professional on smaller screens */
        @media (max-width: 780px) {
            .stApp {
                background:
                    linear-gradient(135deg, #fbfcff 0%, #ffffff 100%);
                animation: none;
            }

            .dashboard-preview-card {
                animation: cardSoftIn 520ms ease-out both;
            }
        }

        @media (prefers-reduced-motion: reduce) {
            .stApp,
            .dashboard-preview-card,
            .tech-pill,
            .proof-pill,
            .support-mini-badge,
            .keyword-pill,
            .roi-badge,
            .nexthire-ai-status,
            .support-data-pill,
            .costops-data-pill {
                animation: none;
            }
        }


        /* -----------------------------
           Step 8.1: Readability Fix
           Keep motion, restore readable professional colors.
        ----------------------------- */

        :root {
            --color-primary: #3d3a8c;
            --color-primary-hover: #302d73;
            --color-primary-subtle: #f1f1fb;
            --color-accent: #8faf9b;
            --color-accent-subtle: #f1f6f3;
            --color-success: #557c5f;
            --color-success-bg: #f1f6f3;
            --color-warning: #9a7435;
            --color-warning-bg: #fbf7ef;
            --color-danger: #9b4a4a;
            --color-danger-bg: #fbf1f1;
            --color-bg: #fafaf9;
            --color-bg-soft: #f4f3f0;
            --color-border: #e8e7e3;
            --color-border-hover: #d7d5cf;
            --color-text-primary: #1c1c1a;
            --color-text-secondary: #5f5e59;
            --color-text-muted: #8b8983;
            --shadow-xs: 0 2px 8px rgba(28, 28, 26, 0.04);
            --shadow-sm: 0 8px 24px rgba(28, 28, 26, 0.07);
            --shadow-md: 0 16px 40px rgba(28, 28, 26, 0.10);
            --shadow-lg: 0 24px 60px rgba(28, 28, 26, 0.12);
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 8%, rgba(61, 58, 140, 0.055), transparent 30%),
                radial-gradient(circle at 92% 14%, rgba(143, 175, 155, 0.055), transparent 28%),
                linear-gradient(135deg, #fafaf9 0%, #f7f6f3 46%, #ffffff 100%);
            background-size: 160% 160%;
            animation: gradientDrift 24s ease infinite;
            color: var(--color-text-primary);
        }

        .topbar {
            background: rgba(255, 255, 255, 0.90);
            backdrop-filter: blur(18px);
            border-color: var(--color-border);
            box-shadow: 0 10px 28px rgba(28, 28, 26, 0.06);
        }

        .brand-title,
        .nav-item,
        .hero-title,
        .why-title,
        .module-title,
        .section-title,
        .support-workflow-title,
        .support-status-title,
        .costops-title,
        .nexthire-title,
        .roi-panel-title,
        [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"],
        h1, h2, h3, h4, h5, h6 {
            -webkit-text-fill-color: initial !important;
            background-image: none !important;
            color: var(--color-text-primary) !important;
            text-shadow: none !important;
        }

        .hero-title span,
        .why-title span,
        .nexthire-score-value.highlight,
        .costops-savings-value.highlight,
        .roi-result-value.highlight,
        .mock-link,
        .cost-row-value {
            -webkit-text-fill-color: initial !important;
            background-image: none !important;
            color: var(--color-primary) !important;
            animation: none !important;
        }

        .hero-copy,
        .section-copy,
        .module-subtitle,
        .why-copy,
        .costops-copy,
        .nexthire-copy,
        .support-workflow-copy,
        .support-status-copy,
        .support-empty-copy,
        .support-report-copy,
        .costops-control-copy,
        .nexthire-control-copy,
        p, li {
            color: var(--color-text-secondary) !important;
        }

        .brand-mark,
        .mock-avatar,
        .value-icon,
        .support-step-num,
        .why-proof-icon,
        .nexthire-signal-icon {
            background: var(--color-primary-subtle) !important;
            color: var(--color-primary) !important;
            box-shadow: none !important;
        }

        .value-icon.sage {
            background: var(--color-accent-subtle) !important;
            color: var(--color-success) !important;
        }

        .value-icon.amber,
        .costops-signal-icon {
            background: var(--color-warning-bg) !important;
            color: var(--color-warning) !important;
        }

        .hero-panel,
        .why-hero-panel,
        .module-header,
        .support-workflow-card,
        .costops-story-card,
        .nexthire-story-card {
            background:
                radial-gradient(circle at 86% 12%, rgba(61, 58, 140, 0.075), transparent 30%),
                radial-gradient(circle at 12% 88%, rgba(143, 175, 155, 0.065), transparent 32%),
                linear-gradient(135deg, #ffffff, #fafaf9) !important;
            border-color: var(--color-border) !important;
        }

        .dashboard-preview-card {
            border-color: var(--color-border) !important;
            box-shadow: var(--shadow-lg) !important;
        }

        .app-card,
        .value-card,
        .metric-card,
        .why-proof-card,
        .support-status-card,
        .support-control-panel,
        .support-empty-card,
        .support-data-banner,
        .support-agent-result,
        .support-report-card,
        .costops-signal-card,
        .costops-control-panel,
        .costops-data-banner,
        .costops-savings-card,
        .costops-report-card,
        .nexthire-signal-card,
        .nexthire-control-panel,
        .nexthire-ai-panel,
        .nexthire-score-card,
        .nexthire-keyword-card,
        .nexthire-list-card,
        .nexthire-report-card,
        [data-testid="stMetric"],
        [data-testid="stPlotlyChart"] {
            background: #ffffff !important;
            border-color: var(--color-border) !important;
            color: var(--color-text-primary) !important;
        }

        .app-card:hover,
        .value-card:hover,
        .metric-card:hover,
        .why-proof-card:hover,
        .support-status-card:hover,
        .support-control-panel:hover,
        .support-data-banner:hover,
        .costops-signal-card:hover,
        .costops-control-panel:hover,
        .costops-data-banner:hover,
        .nexthire-signal-card:hover,
        .nexthire-control-panel:hover,
        .nexthire-ai-panel:hover,
        .nexthire-score-card:hover,
        [data-testid="stMetric"]:hover,
        [data-testid="stPlotlyChart"]:hover {
            transform: translateY(-4px);
            border-color: var(--color-border-hover) !important;
            box-shadow: var(--shadow-md) !important;
        }

        div.stButton > button,
        [data-testid="stDownloadButton"] button {
            background: var(--color-primary) !important;
            border: 1px solid var(--color-primary) !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            box-shadow: 0 10px 24px rgba(61, 58, 140, 0.14) !important;
        }

        div.stButton > button:hover,
        [data-testid="stDownloadButton"] button:hover {
            background: var(--color-primary-hover) !important;
            border-color: var(--color-primary-hover) !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            box-shadow: 0 14px 32px rgba(61, 58, 140, 0.18) !important;
        }

        div.stButton > button p,
        [data-testid="stDownloadButton"] button p {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        .tech-pill,
        .proof-pill,
        .support-mini-badge,
        .keyword-pill,
        .roi-badge,
        .nexthire-ai-status,
        .support-data-pill,
        .costops-data-pill {
            animation: none !important;
            box-shadow: none !important;
            color: var(--color-primary) !important;
            background: var(--color-primary-subtle) !important;
            border-color: rgba(61, 58, 140, 0.14) !important;
        }

        .keyword-pill.good {
            color: var(--color-success) !important;
            background: var(--color-success-bg) !important;
            border-color: rgba(85, 124, 95, 0.18) !important;
        }

        .keyword-pill.gap {
            color: var(--color-danger) !important;
            background: var(--color-danger-bg) !important;
            border-color: rgba(155, 74, 74, 0.18) !important;
        }

        .support-data-pill,
        .costops-data-pill {
            color: var(--color-text-secondary) !important;
            background: var(--color-bg-soft) !important;
            border-color: var(--color-border) !important;
        }

        .section-title::after,
        .module-title::after,
        .support-workflow-title::after,
        .costops-title::after,
        .nexthire-title::after,
        .why-title::after,
        .roi-panel-title::after {
            background: linear-gradient(90deg, var(--color-primary), var(--color-accent)) !important;
            box-shadow: none !important;
        }

        .stTabs [aria-selected="true"] {
            background: var(--color-primary-subtle) !important;
            border-color: rgba(61, 58, 140, 0.22) !important;
            color: var(--color-primary) !important;
            box-shadow: none !important;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: linear-gradient(135deg, #ffffff, #fafaf9) !important;
            border-color: rgba(61, 58, 140, 0.22) !important;
            color: var(--color-text-primary) !important;
        }

        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: rgba(61, 58, 140, 0.38) !important;
            box-shadow: var(--shadow-sm) !important;
        }

        .mock-kpi-good {
            background: var(--color-success-bg) !important;
            color: var(--color-success) !important;
            -webkit-text-fill-color: var(--color-success) !important;
        }

        .mock-sidebar {
            background: linear-gradient(180deg, #3d3a8c 0%, #302d73 100%) !important;
        }

        .mock-side-icon,
        .mock-side-icon.active {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        textarea,
        input,
        .stTextArea textarea,
        .stTextInput input,
        .stNumberInput input {
            color: var(--color-text-primary) !important;
            -webkit-text-fill-color: var(--color-text-primary) !important;
            background: #ffffff !important;
        }

        label[data-testid="stWidgetLabel"] p {
            color: var(--color-text-primary) !important;
            -webkit-text-fill-color: var(--color-text-primary) !important;
        }

        [data-testid="stMetricValue"] {
            color: var(--color-text-primary) !important;
            -webkit-text-fill-color: var(--color-text-primary) !important;
        }

        [data-testid="stMetricLabel"] {
            color: var(--color-text-muted) !important;
            -webkit-text-fill-color: var(--color-text-muted) !important;
        }

        /* Keep readable mode stable on all screens */
        @media (max-width: 780px) {
            .stApp {
                background: linear-gradient(135deg, #fafaf9 0%, #ffffff 100%) !important;
                animation: none !important;
            }
        }


        /* -----------------------------
           Step 9: Smooth Header / No-Box Navigation
           Removes rectangle-looking header and replaces nav buttons with soft HTML pills.
        ----------------------------- */

        .smooth-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.7rem 0 0.35rem 0;
            margin-bottom: 0.25rem;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        .smooth-brand {
            display: flex;
            align-items: center;
            gap: 0.72rem;
            min-width: 0;
        }

        .smooth-logo {
            width: 38px;
            height: 38px;
            border-radius: 999px;
            display: grid;
            place-items: center;
            background:
                radial-gradient(circle at 32% 22%, rgba(255,255,255,0.85), transparent 22%),
                linear-gradient(135deg, #3d3a8c 0%, #6f6baa 58%, #8faf9b 100%);
            color: #ffffff !important;
            font-weight: 800;
            font-size: 0.82rem;
            letter-spacing: -0.06em;
            box-shadow: 0 12px 28px rgba(61, 58, 140, 0.16);
            animation: softFloat 7s ease-in-out infinite;
        }

        .smooth-brand-name {
            color: var(--color-text-primary) !important;
            font-size: 1.28rem;
            line-height: 1;
            font-weight: 700;
            letter-spacing: -0.045em;
        }

        .smooth-brand-name span {
            color: var(--color-primary) !important;
        }

        .smooth-brand-subtitle {
            color: var(--color-text-secondary) !important;
            font-size: 0.76rem;
            margin-top: 0.18rem;
            letter-spacing: -0.005em;
        }

        .smooth-status {
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;
            padding: 0.38rem 0.68rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.62);
            color: var(--color-primary) !important;
            border: 1px solid rgba(61, 58, 140, 0.12);
            font-size: 0.76rem;
            font-weight: 650;
            backdrop-filter: blur(14px);
            box-shadow: 0 8px 22px rgba(28, 28, 26, 0.045);
        }

        .smooth-status-dot {
            width: 7px;
            height: 7px;
            border-radius: 999px;
            background: var(--color-accent);
            box-shadow: 0 0 0 4px rgba(143, 175, 155, 0.15);
            animation: subtlePulse 2.4s ease-in-out infinite;
        }

        .smooth-nav-row {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.48rem;
            margin: 0.65rem 0 1.25rem 0;
            padding: 0;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        .smooth-nav-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 38px;
            padding: 0.55rem 1rem;
            border-radius: 999px;
            text-decoration: none !important;
            color: var(--color-text-secondary) !important;
            background: rgba(255, 255, 255, 0.48);
            border: 1px solid rgba(232, 231, 227, 0.88);
            box-shadow: 0 6px 16px rgba(28, 28, 26, 0.035);
            font-size: 0.85rem;
            font-weight: 650;
            line-height: 1;
            backdrop-filter: blur(12px);
            transition:
                transform 180ms ease,
                background-color 180ms ease,
                border-color 180ms ease,
                color 180ms ease,
                box-shadow 180ms ease;
        }

        .smooth-nav-link:hover {
            color: var(--color-primary) !important;
            background: #ffffff;
            border-color: rgba(61, 58, 140, 0.20);
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(61, 58, 140, 0.075);
        }

        .smooth-nav-link.active {
            color: #ffffff !important;
            background: var(--color-primary);
            border-color: var(--color-primary);
            box-shadow: 0 12px 28px rgba(61, 58, 140, 0.16);
        }

        .smooth-nav-link.active:hover {
            color: #ffffff !important;
            background: var(--color-primary-hover);
            border-color: var(--color-primary-hover);
        }

        .smooth-nav-link span {
            color: inherit !important;
            -webkit-text-fill-color: inherit !important;
        }

        .smooth-nav-link.active span {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        .topbar,
        .nav-helper {
            display: none !important;
        }

        /* Navigation is now HTML pills, so avoid old big rectangular nav button row if browser caches old markup */
        .smooth-nav-row + div[data-testid="stHorizontalBlock"] {
            display: none !important;
        }

        @media (max-width: 780px) {
            .smooth-header {
                align-items: flex-start;
                flex-direction: column;
                gap: 0.65rem;
            }

            .smooth-status {
                align-self: flex-start;
            }

            .smooth-nav-row {
                justify-content: flex-start;
                gap: 0.42rem;
                margin-bottom: 1rem;
            }

            .smooth-nav-link {
                min-height: 36px;
                padding: 0.5rem 0.78rem;
                font-size: 0.8rem;
            }
        }


        /* -----------------------------
           Step 10: Clean SupportOps Input Area
           Removes messy uploader/requirements feel and makes start state product-like.
        ----------------------------- */

        .support-start-shell {
            margin: 1.1rem 0 1rem 0;
            padding: 1.35rem;
            border-radius: 24px;
            background:
                radial-gradient(circle at 92% 8%, rgba(61, 58, 140, 0.075), transparent 32%),
                radial-gradient(circle at 10% 92%, rgba(143, 175, 155, 0.08), transparent 34%),
                #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
        }

        .support-start-title {
            color: var(--color-text-primary) !important;
            font-size: 1.2rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            margin-bottom: 0.35rem;
        }

        .support-start-copy {
            color: var(--color-text-secondary) !important;
            font-size: 0.9rem;
            line-height: 1.58;
            max-width: 760px;
        }

        .support-clean-note {
            margin-top: 0.8rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
        }

        .support-clean-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.36rem 0.58rem;
            border-radius: 999px;
            background: var(--color-primary-subtle);
            color: var(--color-primary) !important;
            border: 1px solid rgba(61, 58, 140, 0.13);
            font-size: 0.74rem;
            font-weight: 650;
        }

        .support-upload-card {
            margin-top: 0.75rem;
            padding: 1rem;
            border-radius: 18px;
            border: 1px solid var(--color-border);
            background: #ffffff;
            box-shadow: var(--shadow-xs);
        }

        .support-upload-title {
            color: var(--color-text-primary) !important;
            font-weight: 700;
            margin-bottom: 0.2rem;
            letter-spacing: -0.015em;
        }

        .support-upload-copy {
            color: var(--color-text-secondary) !important;
            font-size: 0.84rem;
            line-height: 1.52;
            margin-bottom: 0.75rem;
        }

        .support-empty-clean {
            margin-top: 1rem;
            padding: 1.2rem;
            border-radius: 22px;
            background:
                linear-gradient(135deg, rgba(61, 58, 140, 0.04), rgba(143, 175, 155, 0.045)),
                #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        .support-empty-clean-title {
            color: var(--color-text-primary) !important;
            font-size: 1.08rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .support-empty-clean-copy {
            color: var(--color-text-secondary) !important;
            font-size: 0.88rem;
            line-height: 1.55;
        }

        .support-columns-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 0.42rem;
            margin-top: 0.75rem;
        }

        .support-column-pill {
            padding: 0.32rem 0.52rem;
            border-radius: 999px;
            background: var(--color-bg-soft);
            color: var(--color-text-secondary) !important;
            border: 1px solid var(--color-border);
            font-size: 0.72rem;
            font-weight: 600;
        }

        div[data-testid="stExpander"] {
            border: 1px solid var(--color-border) !important;
            border-radius: 16px !important;
            background: rgba(255,255,255,0.74) !important;
            box-shadow: var(--shadow-xs);
            overflow: hidden;
        }

        div[data-testid="stExpander"] summary {
            color: var(--color-text-primary) !important;
            font-weight: 650;
        }


        /* -----------------------------
           Step 11: Product-First SupportOps Start
           Main flow = upload real data. Demo data = optional.
        ----------------------------- */

        :root {
            --support-blue: #2563eb;
            --support-blue-soft: #eff6ff;
            --support-blue-border: #bfdbfe;
            --support-teal: #0f766e;
            --support-teal-soft: #ecfdf5;
            --support-slate: #334155;
            --support-muted: #64748b;
            --support-line: #e2e8f0;
        }

        .support-start-shell,
        .support-empty-clean,
        .support-upload-card {
            display: none !important;
        }

        .support-product-start {
            margin: 1.15rem 0 1.2rem 0;
            padding: 1.35rem;
            border-radius: 24px;
            background:
                radial-gradient(circle at 92% 8%, rgba(37, 99, 235, 0.08), transparent 30%),
                linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid var(--support-line);
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
        }

        .support-product-title {
            color: #0f172a !important;
            font-size: 1.32rem;
            line-height: 1.18;
            font-weight: 750;
            letter-spacing: -0.03em;
            margin-bottom: 0.35rem;
        }

        .support-product-copy {
            color: var(--support-muted) !important;
            font-size: 0.93rem;
            line-height: 1.6;
            max-width: 780px;
        }

        .support-product-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.9fr);
            gap: 1rem;
            align-items: stretch;
            margin-top: 1rem;
        }

        .support-upload-main,
        .support-demo-side {
            padding: 1.1rem;
            border-radius: 20px;
            background: #ffffff;
            border: 1px solid var(--support-line);
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045);
        }

        .support-upload-main {
            border-color: var(--support-blue-border);
            background:
                radial-gradient(circle at 96% 8%, rgba(37, 99, 235, 0.055), transparent 32%),
                #ffffff;
        }

        .support-card-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.28rem 0.55rem;
            border-radius: 999px;
            background: var(--support-blue-soft);
            color: var(--support-blue) !important;
            border: 1px solid var(--support-blue-border);
            font-size: 0.72rem;
            font-weight: 700;
            margin-bottom: 0.6rem;
        }

        .support-card-title {
            color: #0f172a !important;
            font-size: 1rem;
            font-weight: 730;
            letter-spacing: -0.02em;
            margin-bottom: 0.24rem;
        }

        .support-card-copy {
            color: var(--support-muted) !important;
            font-size: 0.84rem;
            line-height: 1.52;
            margin-bottom: 0.75rem;
        }

        .support-help-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.7rem;
            margin-top: 0.85rem;
        }

        .support-help-card {
            padding: 0.85rem;
            border-radius: 16px;
            background: #ffffff;
            border: 1px solid var(--support-line);
        }

        .support-help-icon {
            width: 30px;
            height: 30px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            background: var(--support-blue-soft);
            color: var(--support-blue) !important;
            font-weight: 750;
            margin-bottom: 0.45rem;
        }

        .support-help-title {
            color: #0f172a !important;
            font-size: 0.82rem;
            font-weight: 730;
            margin-bottom: 0.15rem;
        }

        .support-help-copy {
            color: var(--support-muted) !important;
            font-size: 0.74rem;
            line-height: 1.4;
        }

        .support-demo-side {
            background:
                radial-gradient(circle at 92% 12%, rgba(15, 118, 110, 0.065), transparent 30%),
                #ffffff;
        }

        .support-demo-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.28rem 0.55rem;
            border-radius: 999px;
            background: var(--support-teal-soft);
            color: var(--support-teal) !important;
            border: 1px solid rgba(15, 118, 110, 0.16);
            font-size: 0.72rem;
            font-weight: 700;
            margin-bottom: 0.6rem;
        }

        .support-format-box {
            margin-top: 0.85rem;
            padding: 0.85rem;
            border-radius: 16px;
            background: #f8fafc;
            border: 1px solid var(--support-line);
        }

        .support-format-title {
            color: #0f172a !important;
            font-size: 0.82rem;
            font-weight: 730;
            margin-bottom: 0.45rem;
        }

        .support-columns-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 0.36rem;
            margin-top: 0.55rem;
        }

        .support-column-pill {
            padding: 0.28rem 0.48rem;
            border-radius: 999px;
            background: #ffffff;
            color: var(--support-slate) !important;
            border: 1px solid var(--support-line);
            font-size: 0.7rem;
            font-weight: 620;
        }

        .support-waiting-state {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 20px;
            background: #ffffff;
            border: 1px solid var(--support-line);
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
        }

        .support-waiting-title {
            color: #0f172a !important;
            font-size: 1rem;
            font-weight: 730;
            margin-bottom: 0.25rem;
        }

        .support-waiting-copy {
            color: var(--support-muted) !important;
            font-size: 0.85rem;
            line-height: 1.5;
        }

        .support-waiting-copy b {
            color: var(--support-blue) !important;
        }

        /* Make upload area light and readable */
        [data-testid="stFileUploader"] {
            background: #ffffff !important;
            border: 1px solid var(--support-line) !important;
            box-shadow: none !important;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: #ffffff !important;
            border: 1.5px dashed var(--support-blue-border) !important;
            color: #0f172a !important;
        }

        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--support-blue) !important;
            box-shadow: 0 10px 24px rgba(37, 99, 235, 0.08) !important;
        }

        /* Stop old black expander problem */
        div[data-testid="stExpander"],
        div[data-testid="stExpander"] details,
        div[data-testid="stExpander"] summary {
            background: #ffffff !important;
            color: #0f172a !important;
            border-color: var(--support-line) !important;
        }

        @media (max-width: 980px) {
            .support-product-grid,
            .support-help-grid {
                grid-template-columns: 1fr;
            }
        }


        /* -----------------------------
           Step 11.1: SupportOps Upload Button Color Fix
           Keeps file uploader light/readable when opened.
        ----------------------------- */

        /* Expander should stay light even when open */
        div[data-testid="stExpander"],
        div[data-testid="stExpander"] details,
        div[data-testid="stExpander"] details[open],
        div[data-testid="stExpander"] summary {
            background: #ffffff !important;
            color: #0f172a !important;
            border-color: #e2e8f0 !important;
        }

        div[data-testid="stExpander"] summary:hover {
            background: #f8fafc !important;
            color: #0f172a !important;
        }

        div[data-testid="stExpander"] summary p,
        div[data-testid="stExpander"] summary span,
        div[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }

        /* File uploader shell */
        div[data-testid="stFileUploader"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 18px !important;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04) !important;
        }

        div[data-testid="stFileUploaderDropzone"] {
            background:
                linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
            border: 1.5px dashed #bfdbfe !important;
            border-radius: 16px !important;
            color: #0f172a !important;
        }

        div[data-testid="stFileUploaderDropzone"]:hover {
            border-color: #2563eb !important;
            background: #ffffff !important;
            box-shadow: 0 10px 24px rgba(37, 99, 235, 0.08) !important;
        }

        /* Internal uploader button: do not inherit global purple/dark button styles */
        div[data-testid="stFileUploader"] button,
        div[data-testid="stFileUploaderDropzone"] button,
        div[data-testid="stFileUploader"] button:hover,
        div[data-testid="stFileUploaderDropzone"] button:hover,
        div[data-testid="stFileUploader"] button:focus,
        div[data-testid="stFileUploaderDropzone"] button:focus,
        div[data-testid="stFileUploader"] button:active,
        div[data-testid="stFileUploaderDropzone"] button:active {
            background: #ffffff !important;
            color: #2563eb !important;
            -webkit-text-fill-color: #2563eb !important;
            border: 1px solid #bfdbfe !important;
            border-radius: 999px !important;
            box-shadow: none !important;
            font-weight: 700 !important;
            transform: none !important;
        }

        div[data-testid="stFileUploader"] button:hover,
        div[data-testid="stFileUploaderDropzone"] button:hover {
            background: #eff6ff !important;
            border-color: #2563eb !important;
            color: #1d4ed8 !important;
            -webkit-text-fill-color: #1d4ed8 !important;
        }

        div[data-testid="stFileUploader"] button p,
        div[data-testid="stFileUploaderDropzone"] button p,
        div[data-testid="stFileUploader"] button span,
        div[data-testid="stFileUploaderDropzone"] button span {
            color: #2563eb !important;
            -webkit-text-fill-color: #2563eb !important;
        }

        /* File uploader text should never turn dark-on-dark */
        div[data-testid="stFileUploader"] p,
        div[data-testid="stFileUploader"] span,
        div[data-testid="stFileUploader"] small,
        div[data-testid="stFileUploaderDropzone"] p,
        div[data-testid="stFileUploaderDropzone"] span,
        div[data-testid="stFileUploaderDropzone"] small {
            color: #475569 !important;
            -webkit-text-fill-color: #475569 !important;
        }

        div[data-testid="stFileUploader"] label p {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            font-weight: 700 !important;
        }


        /* -----------------------------
           Step 12: NextHire Upload Inputs
           Adds resume/JD upload cards while keeping editable text areas.
        ----------------------------- */

        .nexthire-upload-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 1rem 0 0.75rem 0;
        }

        .nexthire-upload-card {
            padding: 1rem;
            border-radius: 18px;
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        .nexthire-upload-kicker {
            display: inline-flex;
            padding: 0.28rem 0.55rem;
            border-radius: 999px;
            background: var(--color-primary-subtle);
            color: var(--color-primary) !important;
            border: 1px solid rgba(61, 58, 140, 0.14);
            font-size: 0.72rem;
            font-weight: 700;
            margin-bottom: 0.55rem;
        }

        .nexthire-upload-title {
            color: var(--color-text-primary) !important;
            font-size: 0.98rem;
            font-weight: 730;
            letter-spacing: -0.02em;
            margin-bottom: 0.25rem;
        }

        .nexthire-upload-copy {
            color: var(--color-text-secondary) !important;
            font-size: 0.82rem;
            line-height: 1.5;
            margin-bottom: 0.7rem;
        }

        .nexthire-input-note {
            margin: 0.75rem 0 1rem 0;
            padding: 0.85rem 1rem;
            border-radius: 16px;
            background: #ffffff;
            border: 1px solid var(--color-border);
            color: var(--color-text-secondary) !important;
            font-size: 0.84rem;
            line-height: 1.52;
            box-shadow: var(--shadow-xs);
        }

        .nexthire-input-note b {
            color: var(--color-primary) !important;
        }

        @media (max-width: 900px) {
            .nexthire-upload-grid {
                grid-template-columns: 1fr;
            }
        }


        /* -----------------------------
           Step 13: Product Feature Pack
           Templates, guidance, ask-data assistants, and executive reports.
        ----------------------------- */

        .feature-pack-card {
            padding: 1rem;
            border-radius: 18px;
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
            margin: 0.75rem 0;
        }

        .feature-pack-title {
            color: var(--color-text-primary) !important;
            font-size: 1rem;
            font-weight: 730;
            letter-spacing: -0.02em;
            margin-bottom: 0.25rem;
        }

        .feature-pack-copy {
            color: var(--color-text-secondary) !important;
            font-size: 0.84rem;
            line-height: 1.52;
        }

        .template-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.65rem;
        }

        .template-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.34rem 0.56rem;
            border-radius: 999px;
            background: var(--color-bg-soft);
            color: var(--color-text-secondary) !important;
            border: 1px solid var(--color-border);
            font-size: 0.72rem;
            font-weight: 650;
        }

        .ask-card {
            padding: 1.1rem;
            border-radius: 20px;
            background:
                radial-gradient(circle at 92% 10%, rgba(61, 58, 140, 0.055), transparent 32%),
                #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
            margin-bottom: 1rem;
        }

        .ask-card-title {
            color: var(--color-text-primary) !important;
            font-size: 1.05rem;
            font-weight: 730;
            letter-spacing: -0.02em;
            margin-bottom: 0.3rem;
        }

        .ask-card-copy {
            color: var(--color-text-secondary) !important;
            font-size: 0.86rem;
            line-height: 1.52;
        }

        .answer-card {
            padding: 1rem;
            border-radius: 18px;
            background: var(--color-primary-subtle);
            border: 1px solid rgba(61, 58, 140, 0.14);
            color: var(--color-text-primary) !important;
            margin-top: 0.75rem;
            line-height: 1.58;
        }

        .answer-card b {
            color: var(--color-primary) !important;
        }

        .fix-card {
            padding: 1rem;
            border-radius: 18px;
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
            margin-top: 1rem;
        }

        .fix-title {
            color: var(--color-text-primary) !important;
            font-size: 0.95rem;
            font-weight: 730;
            margin-bottom: 0.45rem;
        }

        .fix-list {
            margin: 0;
            padding-left: 1.05rem;
            color: var(--color-text-secondary) !important;
            font-size: 0.84rem;
            line-height: 1.58;
        }

        .template-download-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.7rem;
            margin-top: 0.7rem;
        }

        @media (max-width: 900px) {
            .template-download-grid {
                grid-template-columns: 1fr;
            }
        }


        /* -----------------------------
           Step 14: ProcessOps Analyzer
           Business process bottleneck, rework, and automation opportunity analysis.
        ----------------------------- */

        .processops-story-card,
        .processops-signal-card,
        .processops-start-card,
        .processops-report-card,
        .processops-template-card {
            padding: 1.2rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-sm);
        }

        .processops-story-card {
            background:
                radial-gradient(circle at 88% 16%, rgba(61, 58, 140, 0.07), transparent 30%),
                linear-gradient(135deg, #ffffff, #fafaf9);
        }

        .processops-title {
            color: var(--color-text-primary) !important;
            font-size: 1.15rem;
            font-weight: 730;
            letter-spacing: -0.025em;
            margin-bottom: 0.35rem;
        }

        .processops-copy {
            color: var(--color-text-secondary) !important;
            font-size: 0.9rem;
            line-height: 1.58;
        }

        .processops-signal-list {
            display: grid;
            gap: 0.65rem;
            margin-top: 0.85rem;
        }

        .processops-signal-row {
            display: grid;
            grid-template-columns: 34px 1fr;
            gap: 0.75rem;
            align-items: start;
            padding: 0.72rem;
            border-radius: var(--radius-md);
            background: var(--color-bg-soft);
            border: 1px solid var(--color-border);
        }

        .processops-signal-icon {
            width: 34px;
            height: 34px;
            border-radius: 11px;
            display: grid;
            place-items: center;
            background: var(--color-primary-subtle);
            color: var(--color-primary) !important;
            font-weight: 750;
        }

        .processops-signal-row b {
            color: var(--color-text-primary) !important;
            font-weight: 730;
        }

        .processops-signal-row p {
            color: var(--color-text-secondary) !important;
            margin: 0.15rem 0 0 0;
            font-size: 0.82rem;
            line-height: 1.42;
        }

        .processops-start-card {
            margin: 1rem 0;
            background:
                radial-gradient(circle at 92% 12%, rgba(143, 175, 155, 0.07), transparent 32%),
                #ffffff;
        }

        .processops-help-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.7rem;
            margin-top: 0.9rem;
        }

        .processops-help-card {
            padding: 0.85rem;
            border-radius: 16px;
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        .processops-help-num {
            width: 28px;
            height: 28px;
            border-radius: 10px;
            display: grid;
            place-items: center;
            background: var(--color-primary-subtle);
            color: var(--color-primary) !important;
            font-weight: 750;
            margin-bottom: 0.42rem;
        }

        .processops-help-title {
            color: var(--color-text-primary) !important;
            font-size: 0.82rem;
            font-weight: 730;
            margin-bottom: 0.15rem;
        }

        .processops-help-copy {
            color: var(--color-text-secondary) !important;
            font-size: 0.74rem;
            line-height: 1.42;
        }

        .processops-data-banner {
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 1rem;
            align-items: center;
            margin: 1rem 0;
            padding: 1rem;
            border-radius: var(--radius-lg);
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        .processops-data-title {
            color: var(--color-text-primary) !important;
            font-weight: 730;
            margin-bottom: 0.12rem;
        }

        .processops-data-sub {
            color: var(--color-text-secondary) !important;
            font-size: 0.82rem;
        }

        .processops-data-pill {
            padding: 0.42rem 0.65rem;
            border-radius: var(--radius-full);
            background: var(--color-primary-subtle);
            color: var(--color-primary) !important;
            border: 1px solid rgba(61, 58, 140, 0.14);
            font-size: 0.78rem;
            font-weight: 700;
            white-space: nowrap;
        }

        .processops-tab-note {
            margin: 0.3rem 0 1rem 0;
            padding: 0.85rem 1rem;
            border-radius: var(--radius-md);
            border: 1px solid rgba(61, 58, 140, 0.14);
            background: var(--color-primary-subtle);
            color: var(--color-text-secondary) !important;
            font-size: 0.84rem;
            line-height: 1.52;
        }

        .processops-opportunity-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 1rem 0;
        }

        .processops-opportunity-card {
            padding: 1rem;
            border-radius: 16px;
            background: #ffffff;
            border: 1px solid var(--color-border);
            box-shadow: var(--shadow-xs);
        }

        .processops-opportunity-label {
            color: var(--color-text-secondary) !important;
            font-size: 0.78rem;
            margin-bottom: 0.28rem;
        }

        .processops-opportunity-value {
            color: var(--color-text-primary) !important;
            font-size: 1.25rem;
            font-weight: 730;
            letter-spacing: -0.03em;
        }

        .processops-opportunity-value.highlight {
            color: var(--color-primary) !important;
        }

        @media (max-width: 980px) {
            .processops-help-grid,
            .processops-data-banner,
            .processops-opportunity-grid {
                grid-template-columns: 1fr;
            }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# SHARED COMPONENTS
# =============================================================================

def render_plotly_chart(fig) -> None:
    """Apply a consistent OpsIntel AI chart theme before rendering."""
    fig.update_layout(
        template="plotly_white",
        font=dict(
            family="Inter, Arial, sans-serif",
            color="#1c1c1a",
            size=13,
        ),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#fafaf9",
        title=dict(
            font=dict(size=18, color="#1c1c1a"),
            x=0.02,
            xanchor="left",
        ),
        margin=dict(l=28, r=28, t=72, b=54),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title_text="",
            font=dict(size=12, color="#6b6a66"),
        ),
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#e8e7e3",
            font_size=13,
            font_family="Inter, Arial, sans-serif",
            font_color="#1c1c1a",
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#e8e7e3",
        tickfont=dict(color="#6b6a66", size=12),
        title_font=dict(color="#6b6a66", size=12),
        zeroline=False,
    )
    fig.update_yaxes(
        gridcolor="#efeee9",
        linecolor="#e8e7e3",
        tickfont=dict(color="#6b6a66", size=12),
        title_font=dict(color="#6b6a66", size=12),
        zerolinecolor="#e8e7e3",
    )

    try:
        fig.update_traces(
            marker_line_width=0,
            textfont=dict(color="#1c1c1a", size=12),
            hovertemplate=None,
        )
    except Exception:
        pass

    st.plotly_chart(fig, width="stretch")

def render_topbar() -> None:
    """Render smooth no-box website header and navigation."""
    current_page = st.session_state.get("page", "Home")

    def nav_link(label: str, page_name: str) -> str:
        slug = PAGE_TO_SLUG.get(page_name, "home")
        active = " active" if current_page == page_name else ""
        return f'<a class="smooth-nav-link{active}" href="?page={slug}" target="_self"><span>{label}</span></a>'

    nav_html = f"""
<div class="smooth-header">
  <div class="smooth-brand">
    <div class="smooth-logo">OI</div>
    <div>
      <div class="smooth-brand-name">OpsIntel <span>AI</span></div>
      <div class="smooth-brand-subtitle">AI intelligence for support, spend, and hiring workflows</div>
    </div>
  </div>
  <div class="smooth-status">
    <span class="smooth-status-dot"></span>
    <span>Live portfolio product</span>
  </div>
</div>

<div class="smooth-nav-row">
  {nav_link("Home", "Home")}
  {nav_link("Why Us", "Why Us")}
  {nav_link("SupportOps", "SupportOps Analyzer")}
  {nav_link("CostOps", "CostOps Analyzer")}
  {nav_link("NextHire AI", "NextHire AI")}
  {nav_link("ProcessOps", "ProcessOps Analyzer")}
</div>
"""
    st.markdown(nav_html, unsafe_allow_html=True)

def render_footer() -> None:
    """Render the footer."""
    st.markdown(
        """
        <div class="ops-footer">
            <div class="footer-grid">
                <div>
                    <div class="footer-brand">
                        <div class="footer-mini-logo"></div>
                        <b>OpsIntel AI</b>
                    </div>
                    AI-powered intelligence for modern support, finance, and hiring operations.
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
                    Recruiter-ready reports
                </div>
                <div>
                    <b>Built With</b><br>
                    Python • Streamlit • Pandas<br>
                    Plotly charts<br>
                    Gemini LLM agents
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
    return generate_cost_executive_report(df)


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

def _extract_json_response(text: str) -> dict:
    """Extract JSON safely from a Gemini response."""
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


def generate_nexthire_ai_feedback(
    resume_text: str,
    jd_text: str,
    score: int,
    matched: list[str],
    missing: list[str],
) -> dict:
    """
    Generate recruiter-facing hiring decision support using Gemini.
    Falls back to keyword-based hiring feedback if Gemini is unavailable.
    """
    fallback = {
        "overall_feedback": (
            f"The candidate has a {score}/100 match with the role requirements. "
            "The profile shows relevant signals, but the hiring team should validate hands-on experience, business impact, and the missing role requirements before moving forward."
        ),
        "strengths": matched[:8],
        "gaps": missing[:8],
        "resume_improvements": [
            "Review the missing role keywords before shortlisting the candidate.",
            "Validate hands-on experience for the most important required tools and responsibilities.",
            "Ask for measurable examples such as time saved, cost reduced, accuracy improved, or reports automated.",
            "Check whether the candidate has end-to-end experience from raw data to business recommendation.",
            "Use stakeholder, documentation, KPI reporting, and process-improvement questions during the interview.",
        ],
        "interview_questions": [
            "Tell me about a time you improved a business process.",
            "How do you gather and document requirements from stakeholders?",
            "How would you analyze SLA, cost, or performance data?",
            "What dashboards or reports have you built, and who used them?",
            "How do you explain technical findings to non-technical stakeholders?",
        ],
        "agent_trace": [
            "Generated fallback keyword-based NextHire hiring briefing.",
        ],
    }

    if not os.getenv("GEMINI_API_KEY"):
        fallback["agent_trace"].append("GEMINI_API_KEY not found. Used fallback mode.")
        return fallback

    prompt = f"""
You are an expert recruiter, hiring manager, and business analyst hiring advisor.

Analyze the candidate profile against the role requirements.
Return ONLY valid JSON.
Do not include markdown.
Do not include explanations outside JSON.

Use this exact JSON schema:

{{
  "overall_feedback": "clear recruiter-facing hiring summary",
  "strengths": ["candidate strength 1", "candidate strength 2", "candidate strength 3"],
  "gaps": ["hiring gap or risk 1", "hiring gap or risk 2", "hiring gap or risk 3"],
  "resume_improvements": ["recruiter recommendation 1", "recruiter recommendation 2", "recruiter recommendation 3", "recruiter recommendation 4", "recruiter recommendation 5"],
  "interview_questions": ["structured interview question 1", "structured interview question 2", "structured interview question 3", "structured interview question 4", "structured interview question 5"],
  "agent_trace": ["step 1", "step 2", "step 3"]
}}

Rules:
- Be honest, practical, and recruiter-oriented.
- Do not invent experience that is not in the candidate profile.
- Focus on hiring decision support, not personal resume coaching.
- Identify strengths, gaps, risks, and validation questions.
- Focus on business analyst, operations analyst, data analyst, implementation, and project-oriented roles.
- Return only valid JSON.

Candidate-role match score: {score}/100

Matched keywords:
{matched}

Missing keywords:
{missing}

Candidate profile:
{resume_text}

Role requirements:
{jd_text}
"""

    try:
        client = genai.Client()
        model = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        result = _extract_json_response(response.text)

        # Keep stable internal keys so the dashboard does not crash if Gemini omits a field.
        result.setdefault("overall_feedback", fallback["overall_feedback"])
        result.setdefault("strengths", fallback["strengths"])
        result.setdefault("gaps", fallback["gaps"])
        result.setdefault("resume_improvements", fallback["resume_improvements"])
        result.setdefault("interview_questions", fallback["interview_questions"])
        result.setdefault("agent_trace", [])

        result["agent_trace"].append(f"Gemini NextHire hiring briefing completed using {model}.")
        return result

    except Exception as error:
        fallback["agent_trace"].append(f"Gemini NextHire hiring briefing failed. Fallback used. Error: {error}")
        return fallback

def generate_nexthire_report(score: int, matched: list[str], missing: list[str]) -> str:
    """Generate a recruiter-facing hiring report."""
    return f"""OpsIntel AI - NextHire Hiring Report

Candidate-Role Match Score: {score}/100

Matched Role Keywords:
{", ".join(matched[:20])}

Missing / Weak Role Keywords:
{", ".join(missing[:20])}

Recruiter Recommendations:
1. Review the missing role keywords before moving the candidate forward.
2. Validate the candidate's hands-on experience with the most important required skills.
3. Ask for examples of measurable business impact, such as time saved, cost reduced, accuracy improved, or reports automated.
4. Check whether the candidate has end-to-end experience from raw data to business recommendation.
5. Use structured interview questions to confirm stakeholder, analytics, and communication skills.

Structured Interview Questions:
1. Tell me about a time you improved a business process.
2. How do you gather and document requirements from stakeholders?
3. How would you analyze SLA, cost, or performance data?
4. What dashboards or reports have you built?
5. How do you communicate insights to non-technical stakeholders?
"""

# =============================================================================
# PAGES
# =============================================================================
def render_home_page() -> None:
    """Render polished SaaS-style home page."""
    st.markdown('<div class="hero-shell">', unsafe_allow_html=True)

    hero_left, hero_right = st.columns([0.88, 1.12], gap="large")

    with hero_left:
        st.markdown(
            """
            <div class="hero-panel">
                <div class="eyebrow">✦ AI Operations Intelligence Platform</div>
                <div class="hero-title">
                    One platform for operations, cost, and hiring <span>intelligence.</span>
                </div>
                <div class="hero-copy">
                    OpsIntel AI connects business data, surfaces what matters, and delivers
                    actionable insights across support, spend, and talent operations.
                </div>
            """,
            unsafe_allow_html=True,
        )

        cta1, cta2 = st.columns([1, 1])
        if cta1.button("Explore Platform", key="hero_explore", width="stretch"):
            go_to("Why Us")
        if cta2.button("View Live Demo", key="hero_demo", width="stretch"):
            enable_support_demo()

        st.markdown(
            """
                <div class="hero-cta-note">Start with the demo dataset, then upload your own business data.</div>
                <div class="tech-strip">
                    <div class="tech-pill"><span class="tech-dot"></span> Python</div>
                    <div class="tech-pill"><span class="tech-dot sage"></span> Streamlit</div>
                    <div class="tech-pill"><span class="tech-dot amber"></span> Pandas</div>
                    <div class="tech-pill"><span class="tech-dot"></span> Plotly</div>
                    <div class="tech-pill"><span class="tech-dot sage"></span> Gemini</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with hero_right:
        dashboard_preview_html = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
:root {
  --primary: #3d3a8c;
  --primary-2: #6f6baa;
  --sage: #8faf9b;
  --sage-dark: #557c5f;
  --bg: #fafaf9;
  --surface: #ffffff;
  --border: #e8e7e3;
  --border-2: #d7d5cf;
  --text: #1c1c1a;
  --muted: #6b6a66;
  --soft: #f4f3f0;
  --shadow: 0 24px 60px rgba(28, 28, 26, 0.10);
}
* {
  box-sizing: border-box;
}
html, body {
  margin: 0;
  padding: 0;
  background: transparent;
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--text);
}
.dashboard-preview-card {
  min-height: 514px;
  padding: 1rem;
  border-radius: 30px;
  background: #ffffff;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.dashboard-browser {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.45rem 0.9rem 0.45rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.85rem;
}
.browser-dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: #ddd8cf;
}
.browser-dot.red { background: #df8f83; }
.browser-dot.amber { background: #d8b36f; }
.browser-dot.green { background: #8faf9b; }
.browser-url {
  margin-left: auto;
  margin-right: auto;
  padding: 0.28rem 2rem;
  border-radius: 999px;
  background: var(--bg);
  color: #8b8983;
  font-size: 0.74rem;
}
.mock-layout {
  display: grid;
  grid-template-columns: 54px 1fr;
  gap: 0.85rem;
}
.mock-sidebar {
  min-height: 420px;
  border-radius: 16px;
  background: linear-gradient(180deg, #3d3a8c 0%, #2f2c6d 100%);
  padding: 0.55rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
}
.mock-side-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  color: rgba(255,255,255,0.82);
  font-size: 0.9rem;
}
.mock-side-icon.active {
  background: rgba(255,255,255,0.16);
  color: #ffffff;
}
.mock-avatar {
  margin-top: auto;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  background: #eff5f1;
  color: #557c5f;
  display: grid;
  place-items: center;
  font-size: 0.72rem;
  font-weight: 700;
}
.mock-main {
  min-width: 0;
}
.mock-topline {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}
.mock-title {
  color: var(--text);
  font-size: 1rem;
  font-weight: 650;
}
.mock-sub {
  color: #8b8983;
  font-size: 0.75rem;
}
.mock-date {
  padding: 0.43rem 0.65rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--muted);
  font-size: 0.72rem;
  background: #ffffff;
  white-space: nowrap;
}
.mock-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.58rem;
  margin-bottom: 0.78rem;
}
.mock-kpi {
  padding: 0.72rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: #ffffff;
}
.mock-kpi-label {
  color: #8b8983;
  font-size: 0.68rem;
  margin-bottom: 0.28rem;
}
.mock-kpi-value {
  color: var(--text);
  font-size: 1.2rem;
  font-weight: 650;
  letter-spacing: -0.03em;
}
.mock-kpi-good {
  display: inline-flex;
  margin-top: 0.38rem;
  padding: 0.16rem 0.36rem;
  border-radius: 999px;
  background: #eff5f1;
  color: #557c5f;
  font-size: 0.64rem;
  font-weight: 600;
}
.mock-lower {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 0.75rem;
}
.mock-chart-card,
.mock-activity-card {
  border: 1px solid var(--border);
  border-radius: 14px;
  background: #ffffff;
  padding: 0.85rem;
  min-height: 205px;
}
.mock-card-heading {
  font-size: 0.82rem;
  font-weight: 650;
  color: var(--text);
  margin-bottom: 0.55rem;
}
.mock-chart {
  height: 140px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background:
    linear-gradient(180deg, rgba(61, 58, 140, 0.05), transparent),
    repeating-linear-gradient(
      to right,
      transparent 0,
      transparent 38px,
      rgba(232, 231, 227, 0.62) 38px,
      rgba(232, 231, 227, 0.62) 39px
    );
  position: relative;
  overflow: hidden;
}
.mock-chart::before {
  content: "";
  position: absolute;
  left: 18px;
  right: 18px;
  top: 62px;
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(90deg, #3d3a8c, #6f6baa, #8faf9b);
  transform: skewY(-7deg);
  box-shadow:
    42px -18px 0 -1px rgba(61,58,140,0.72),
    96px 13px 0 -1px rgba(143,175,155,0.72),
    145px -12px 0 -1px rgba(154,116,53,0.46);
}
.mock-activity {
  display: grid;
  gap: 0.55rem;
}
.mock-activity-row {
  display: grid;
  grid-template-columns: 24px 1fr auto;
  gap: 0.45rem;
  align-items: center;
}
.mock-activity-icon {
  width: 24px;
  height: 24px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: rgba(61, 58, 140, 0.08);
  color: var(--primary);
  font-size: 0.72rem;
}
.mock-activity-text {
  color: var(--muted);
  font-size: 0.72rem;
}
.mock-activity-time {
  color: #8b8983;
  font-size: 0.66rem;
}
.mock-link {
  color: var(--primary);
  font-size: 0.76rem;
  font-weight: 600;
  margin-top: 0.8rem;
}
@media (max-width: 760px) {
  .dashboard-preview-card {
    min-height: auto;
  }
  .mock-layout {
    grid-template-columns: 1fr;
  }
  .mock-sidebar {
    display: none;
  }
  .mock-kpis,
  .mock-lower {
    grid-template-columns: 1fr;
  }
}
</style>
</head>
<body>
  <div class="dashboard-preview-card">
    <div class="dashboard-browser">
      <span class="browser-dot red"></span>
      <span class="browser-dot amber"></span>
      <span class="browser-dot green"></span>
      <span class="browser-url">opsintel.ai</span>
    </div>

    <div class="mock-layout">
      <div class="mock-sidebar">
        <div class="mock-side-icon active">⌂</div>
        <div class="mock-side-icon">▥</div>
        <div class="mock-side-icon">$</div>
        <div class="mock-side-icon">◌</div>
        <div class="mock-side-icon">⚙</div>
        <div class="mock-avatar">AI</div>
      </div>

      <div class="mock-main">
        <div class="mock-topline">
          <div>
            <div class="mock-title">Overview</div>
            <div class="mock-sub">Real-time summary of your operations.</div>
          </div>
          <div class="mock-date">May 12 – May 18, 2026</div>
        </div>

        <div class="mock-kpis">
          <div class="mock-kpi">
            <div class="mock-kpi-label">Total Tickets</div>
            <div class="mock-kpi-value">12,842</div>
            <div class="mock-kpi-good">▲ 8.6%</div>
          </div>
          <div class="mock-kpi">
            <div class="mock-kpi-label">Avg Resolution</div>
            <div class="mock-kpi-value">18.6h</div>
            <div class="mock-kpi-good">▼ 11.2%</div>
          </div>
          <div class="mock-kpi">
            <div class="mock-kpi-label">Cost Leak</div>
            <div class="mock-kpi-value">$248K</div>
            <div class="mock-kpi-good">▲ 9.3%</div>
          </div>
          <div class="mock-kpi">
            <div class="mock-kpi-label">Profiles</div>
            <div class="mock-kpi-value">3,421</div>
            <div class="mock-kpi-good">▲ 24.7%</div>
          </div>
        </div>

        <div class="mock-lower">
          <div class="mock-chart-card">
            <div class="mock-card-heading">Trends</div>
            <div class="mock-chart"></div>
            <div class="mock-link">View full dashboard →</div>
          </div>

          <div class="mock-activity-card">
            <div class="mock-card-heading">Recent Activity</div>
            <div class="mock-activity">
              <div class="mock-activity-row">
                <div class="mock-activity-icon">!</div>
                <div class="mock-activity-text">High cost leak detected</div>
                <div class="mock-activity-time">2m</div>
              </div>
              <div class="mock-activity-row">
                <div class="mock-activity-icon">↗</div>
                <div class="mock-activity-text">Billing ticket spike</div>
                <div class="mock-activity-time">15m</div>
              </div>
              <div class="mock-activity-row">
                <div class="mock-activity-icon">◎</div>
                <div class="mock-activity-text">Candidate batch screened</div>
                <div class="mock-activity-time">1h</div>
              </div>
              <div class="mock-activity-row">
                <div class="mock-activity-icon">◆</div>
                <div class="mock-activity-text">Storage spend anomaly</div>
                <div class="mock-activity-time">2h</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</body>
</html>
"""
        components.html(dashboard_preview_html, height=540, scrolling=False)


    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">Choose an application</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Four focused modules. Each application has a clear workflow, upload path, assistant, report output, and business value.</div>',
        unsafe_allow_html=True,
    )

    app_row1_col1, app_row1_col2 = st.columns(2, gap="large")

    with app_row1_col1:
        st.markdown(
            """
            <div class="app-card">
                <div class="app-card-top">
                    <div class="icon-box sage">🎧</div>
                    <div>
                        <div class="app-title">SupportOps Analyzer</div>
                        <div class="app-copy">
                            Analyze support performance, SLA risk, customer frustration,
                            escalation pressure, and agent workload.
                        </div>
                    </div>
                </div>
                <div class="value-list">
                    • Reduce ticket rework<br>
                    • Prioritize risky customers<br>
                    • Generate manager briefings
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Explore SupportOps →", key="home_support", width="stretch"):
            go_to("SupportOps Analyzer")

    with app_row1_col2:
        st.markdown(
            """
            <div class="app-card">
                <div class="app-card-top">
                    <div class="icon-box amber">💰</div>
                    <div>
                        <div class="app-title">CostOps Analyzer</div>
                        <div class="app-copy">
                            Uncover cost leaks, track budget variance, find vendor concentration,
                            and prioritize savings opportunities.
                        </div>
                    </div>
                </div>
                <div class="value-list">
                    • Detect overspending<br>
                    • Find avoidable variance<br>
                    • Download savings reports
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Explore CostOps →", key="home_cost", width="stretch"):
            go_to("CostOps Analyzer")

    app_row2_col1, app_row2_col2 = st.columns(2, gap="large")

    with app_row2_col1:
        st.markdown(
            """
            <div class="app-card">
                <div class="app-card-top">
                    <div class="icon-box">🧠</div>
                    <div>
                        <div class="app-title">NextHire AI</div>
                        <div class="app-copy">
                            Upload or paste resumes and role requirements, calculate fit,
                            identify gaps, and create hiring reports.
                        </div>
                    </div>
                </div>
                <div class="value-list">
                    • Upload resume/JD files<br>
                    • Improve candidate review<br>
                    • Generate hiring briefings
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Explore NextHire AI →", key="home_hire", width="stretch"):
            go_to("NextHire AI")

    with app_row2_col2:
        st.markdown(
            """
            <div class="app-card">
                <div class="app-card-top">
                    <div class="icon-box sage">🔁</div>
                    <div>
                        <div class="app-title">ProcessOps Analyzer</div>
                        <div class="app-copy">
                            Analyze process logs to find bottlenecks, approval delays,
                            rework loops, owner workload, and automation opportunities.
                        </div>
                    </div>
                </div>
                <div class="value-list">
                    • Find process bottlenecks<br>
                    • Reduce approval delays<br>
                    • Generate improvement reports
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Explore ProcessOps →", key="home_process", width="stretch"):
            go_to("ProcessOps Analyzer")

    st.markdown(
        """
        <div class="home-impact-strip">
            <div class="impact-title">Why teams use OpsIntel AI</div>
            <div class="impact-grid">
                <div class="impact-item">
                    <div class="impact-icon">↗</div>
                    <div>
                        <div class="impact-number">5–15%</div>
                        <div class="impact-label">potential support rework reduction</div>
                    </div>
                </div>
                <div class="impact-item">
                    <div class="impact-icon">$</div>
                    <div>
                        <div class="impact-number">8–12%</div>
                        <div class="impact-label">potential spend leak discovery</div>
                    </div>
                </div>
                <div class="impact-item">
                    <div class="impact-icon">◎</div>
                    <div>
                        <div class="impact-number">30–50%</div>
                        <div class="impact-label">manual screening time reduction</div>
                    </div>
                </div>
                <div class="impact-item">
                    <div class="impact-icon">↻</div>
                    <div>
                        <div class="impact-number">Process</div>
                        <div class="impact-label">bottleneck detection and automation ideas</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_footer()

def render_why_us_page() -> None:
    """Render polished Why Us page."""
    why_left, why_right = st.columns([1.08, 0.92], gap="large")

    with why_left:
        why_left_html = """
<div class="why-hero-panel">
  <div class="why-kicker">Business value layer</div>
  <div class="why-title">
    Stop losing money in <span>manual operations review.</span>
  </div>
  <div class="why-copy">
    OpsIntel AI helps teams convert scattered support, spend, and hiring data into
    clear risk signals, savings opportunities, and action-ready reports. The goal is not
    just prettier dashboards — it is faster decisions, fewer missed issues, and less
    manual review work.
  </div>
</div>
"""
        st.markdown(why_left_html, unsafe_allow_html=True)

    with why_right:
        why_right_html = """
<div class="why-proof-card">
  <div class="why-proof-title">Where companies usually lose value</div>
  <div class="why-proof-list">
    <div class="why-proof-row">
      <div class="why-proof-icon">01</div>
      <div>
        <b>Support issues are found too late</b>
        <p>SLA breaches, repeat contacts, and negative sentiment become expensive escalations.</p>
      </div>
    </div>
    <div class="why-proof-row">
      <div class="why-proof-icon">02</div>
      <div>
        <b>Spend leaks stay hidden</b>
        <p>Budget variance, vendor concentration, and recurring overspend are hard to spot manually.</p>
      </div>
    </div>
    <div class="why-proof-row">
      <div class="why-proof-icon">03</div>
      <div>
        <b>Hiring review takes too long</b>
        <p>Recruiters and managers spend time screening profiles before identifying real fit.</p>
      </div>
    </div>
  </div>
</div>
"""
        st.markdown(why_right_html, unsafe_allow_html=True)

    st.markdown('<div class="section-title">How OpsIntel AI creates measurable value</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">These are example business-impact estimates. Actual results depend on team size, data quality, and execution.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
<div class="value-card">
  <div class="value-icon sage">↗</div>
  <div class="value-number">5–15%</div>
  <div class="value-label">Potential support rework reduction</div>
  <div class="value-note">
    Earlier visibility into SLA breaches, repeat contacts, and sentiment risk can help reduce escalation handling and manual follow-up.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
<div class="value-card">
  <div class="value-icon amber">$</div>
  <div class="value-number">8–12%</div>
  <div class="value-label">Potential avoidable spend discovery</div>
  <div class="value-note">
    CostOps highlights budget variance, recurring overspend, unused categories, and vendor concentration patterns.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
<div class="value-card">
  <div class="value-icon">◎</div>
  <div class="value-number">30–50%</div>
  <div class="value-label">Manual screening time reduction</div>
  <div class="value-note">
    NextHire AI can pre-score candidate profiles against role requirements so hiring teams can focus on real fit faster.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
<div class="cost-leak-panel">
  <div class="cost-leak-grid">
    <div>
      <div class="cost-leak-title">What the platform helps surface</div>
      <div class="cost-leak-copy">
        OpsIntel AI is designed for the messy middle layer of business operations:
        the place where support issues, cost variance, and hiring gaps exist in data,
        but are not always turned into timely decisions.
      </div>
    </div>
    <div>
      <div class="cost-row">
        <div class="cost-row-label">SupportOps</div>
        <div class="cost-row-value">SLA risk + escalation signals</div>
      </div>
      <div class="cost-row">
        <div class="cost-row-label">CostOps</div>
        <div class="cost-row-value">Variance + savings opportunities</div>
      </div>
      <div class="cost-row">
        <div class="cost-row-label">NextHire AI</div>
        <div class="cost-row-value">Match score + hiring gaps</div>
      </div>
      <div class="cost-row">
        <div class="cost-row-label">Reports</div>
        <div class="cost-row-value">Manager-ready action plans</div>
      </div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="roi-panel">
  <div class="roi-panel-header">
    <div>
      <div class="roi-panel-title">Simple ROI example</div>
      <div class="roi-panel-subtitle">
        Adjust the assumptions below to see how operational savings and time savings can combine into monthly value.
      </div>
    </div>
    <div class="roi-badge">Interactive calculator</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    roi_cols = st.columns(3)
    monthly_cost = roi_cols[0].number_input(
        "Monthly operational cost reviewed ($)",
        min_value=1000,
        value=50000,
        step=1000,
    )
    avoidable_pct = roi_cols[1].slider(
        "Estimated avoidable waste found (%)",
        min_value=1,
        max_value=20,
        value=8,
    )
    time_saved_hours = roi_cols[2].slider(
        "Manual review hours saved / month",
        min_value=1,
        max_value=100,
        value=20,
    )

    monthly_savings = monthly_cost * avoidable_pct / 100
    labor_savings = time_saved_hours * 35
    total_value = monthly_savings + labor_savings

    st.markdown(
        f"""
<div class="roi-results-grid">
  <div class="roi-result">
    <div class="roi-result-label">Estimated cost savings</div>
    <div class="roi-result-value">${monthly_savings:,.0f}/mo</div>
  </div>
  <div class="roi-result">
    <div class="roi-result-label">Estimated labor value</div>
    <div class="roi-result-value">${labor_savings:,.0f}/mo</div>
  </div>
  <div class="roi-result">
    <div class="roi-result-label">Total estimated value</div>
    <div class="roi-result-value highlight">${total_value:,.0f}/mo</div>
  </div>
</div>
<div class="why-disclaimer">
  This ROI calculator is a portfolio demo. It shows business value thinking, not a guaranteed financial result.
  Real results depend on implementation quality, adoption, data accuracy, and operational discipline.
</div>
""",
        unsafe_allow_html=True,
    )

    render_footer()


# =============================================================================
# PRODUCT FEATURE PACK HELPERS
# =============================================================================
def get_support_template_df() -> pd.DataFrame:
    """Return a downloadable SupportOps CSV template."""
    return pd.DataFrame(
        [
            {
                "ticket_id": "T-1001",
                "customer_id": "C-501",
                "department": "Billing",
                "issue_type": "Refund Delay",
                "priority": "High",
                "agent": "Maya",
                "channel": "Email",
                "created_at": "2026-06-01 09:30:00",
                "first_response_at": "2026-06-01 10:10:00",
                "resolved_at": "2026-06-02 15:00:00",
                "status": "Closed",
                "sla_breached": "Yes",
                "customer_rating": 2,
                "sentiment": "Negative",
                "escalated": "Yes",
            },
            {
                "ticket_id": "T-1002",
                "customer_id": "C-502",
                "department": "Technical Support",
                "issue_type": "Login Issue",
                "priority": "Medium",
                "agent": "Ravi",
                "channel": "Chat",
                "created_at": "2026-06-01 11:15:00",
                "first_response_at": "2026-06-01 11:20:00",
                "resolved_at": "2026-06-01 14:40:00",
                "status": "Closed",
                "sla_breached": "No",
                "customer_rating": 4,
                "sentiment": "Positive",
                "escalated": "No",
            },
        ]
    )


def get_cost_template_df() -> pd.DataFrame:
    """Return a downloadable CostOps CSV template."""
    return pd.DataFrame(
        [
            {
                "date": "2026-06-01",
                "department": "IT",
                "cost_category": "Cloud Compute",
                "vendor": "AWS",
                "budget_amount": 42000,
                "actual_amount": 51500,
                "project_name": "Cloud Platform",
                "region": "US",
                "owner": "Ravi",
                "business_unit": "Technology",
            },
            {
                "date": "2026-06-01",
                "department": "Operations",
                "cost_category": "Logistics",
                "vendor": "FedEx",
                "budget_amount": 36000,
                "actual_amount": 39800,
                "project_name": "Delivery Ops",
                "region": "US",
                "owner": "Kim",
                "business_unit": "Operations",
            },
        ]
    )


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a dataframe to downloadable CSV bytes."""
    return df.to_csv(index=False).encode("utf-8")


def support_quality_suggestions(quality: dict, column_check: dict) -> list[str]:
    """Generate practical fix suggestions for SupportOps uploads."""
    suggestions = []

    if not column_check.get("passed", False):
        missing = column_check.get("missing_columns", [])
        suggestions.append(f"Add missing required columns: {', '.join(missing)}.")

    if quality.get("missing_value_total", 0) > 0:
        suggestions.append("Fill missing values in priority, department, issue type, agent, status, and date fields before analysis.")

    if quality.get("duplicate_ticket_count", 0) > 0:
        suggestions.append("Remove duplicate ticket IDs so the same issue is not counted multiple times.")

    if quality.get("invalid_date_count", 0) > 0:
        suggestions.append("Fix invalid date values. Use a consistent format such as YYYY-MM-DD HH:MM:SS.")

    if not suggestions:
        suggestions.append("Data looks analysis-ready. Move to Overview and SLA & Risk tabs for operational insights.")

    return suggestions


def cost_quality_suggestions(df: pd.DataFrame, missing: set[str]) -> list[str]:
    """Generate practical fix suggestions for CostOps uploads."""
    suggestions = []

    if missing:
        suggestions.append(f"Add missing required columns: {', '.join(sorted(missing))}.")

    for col in ["budget_amount", "actual_amount"]:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            if numeric.isna().sum() > 0:
                suggestions.append(f"Clean non-numeric values in {col}. This column should contain only numbers.")

    if "date" in df.columns:
        invalid_dates = pd.to_datetime(df["date"], errors="coerce").isna().sum()
        if invalid_dates > 0:
            suggestions.append("Fix invalid date values. Use YYYY-MM-DD format for clean monthly trend analysis.")

    if {"budget_amount", "actual_amount"}.issubset(df.columns):
        budgets = pd.to_numeric(df["budget_amount"], errors="coerce")
        if (budgets <= 0).sum() > 0:
            suggestions.append("Review rows with zero or negative budget values. Variance percentage needs a positive budget.")

    if not suggestions:
        suggestions.append("Cost data looks analysis-ready. Review Spend Overview and Savings Report tabs.")

    return suggestions


def answer_support_question(question: str, df: pd.DataFrame) -> str:
    """Simple rule-based assistant for SupportOps data."""
    q = question.lower().strip()
    if not q:
        return "Ask a question such as: Which department has the highest SLA risk?"

    kpis = calculate_kpis(df)
    top_dept = sla_summary_by_department(df).sort_values("sla_breach_rate", ascending=False).iloc[0]
    top_issues = issue_type_summary(df).sort_values("total_tickets", ascending=False).head(3)
    high_risk = top_high_risk_tickets(df).head(5)

    if "sla" in q or "breach" in q:
        return (
            f"<b>SLA risk:</b> The highest SLA breach rate is in <b>{top_dept['department']}</b> "
            f"at <b>{top_dept['sla_breach_rate']}%</b>. Overall SLA breach rate is "
            f"<b>{kpis['sla_breach_rate']}%</b>. Start by reviewing high-priority tickets in this department."
        )

    if "department" in q or "team" in q:
        return (
            f"<b>Department focus:</b> <b>{top_dept['department']}</b> needs the most attention based on SLA breach rate. "
            "Use the SLA & Risk tab to compare departments and identify where coaching, staffing, or process fixes may help."
        )

    if "issue" in q or "driver" in q or "reason" in q:
        issues = ", ".join([f"{row.issue_type} ({row.total_tickets})" for row in top_issues.itertuples()])
        return f"<b>Top issue drivers:</b> {issues}. These categories should be reviewed for recurring root causes."

    if "risk" in q or "high" in q or "priority" in q:
        ids = ", ".join(high_risk["ticket_id"].astype(str).tolist())
        return f"<b>High-risk tickets:</b> Start with these tickets: {ids}. They likely combine SLA, escalation, sentiment, or priority pressure."

    if "sentiment" in q or "customer" in q or "frustration" in q:
        return (
            f"<b>Customer sentiment:</b> Negative sentiment rate is <b>{kpis['negative_sentiment_rate']}%</b>. "
            "Focus on repeat issue types, escalated tickets, and low customer ratings."
        )

    return (
        f"<b>Summary:</b> Total tickets: <b>{kpis['total_tickets']:,}</b>, open tickets: <b>{kpis['open_tickets']:,}</b>, "
        f"SLA breach rate: <b>{kpis['sla_breach_rate']}%</b>, high-risk tickets: <b>{kpis['high_risk_tickets']:,}</b>. "
        "Ask about SLA, departments, issue drivers, sentiment, or high-risk tickets for a more specific answer."
    )


def answer_cost_question(question: str, df: pd.DataFrame) -> str:
    """Simple rule-based assistant for CostOps data."""
    q = question.lower().strip()
    if not q:
        return "Ask a question such as: Which vendor is causing the most spend?"

    total_spend = df["actual_amount"].sum()
    total_budget = df["budget_amount"].sum()
    variance = total_spend - total_budget
    savings = df["savings_opportunity"].sum()

    dept = df.groupby("department", as_index=False)["variance"].sum().sort_values("variance", ascending=False)
    vendor = df.groupby("vendor", as_index=False)["actual_amount"].sum().sort_values("actual_amount", ascending=False)
    category = df.groupby("cost_category", as_index=False)["variance"].sum().sort_values("variance", ascending=False)

    if "vendor" in q:
        row = vendor.iloc[0]
        return f"<b>Vendor concentration:</b> <b>{row['vendor']}</b> has the highest spend at <b>${row['actual_amount']:,.0f}</b>. Review contract terms, usage, and consolidation options."

    if "department" in q or "team" in q:
        row = dept.iloc[0]
        return f"<b>Department variance:</b> <b>{row['department']}</b> has the highest over-budget variance at <b>${row['variance']:,.0f}</b>."

    if "category" in q or "driver" in q:
        row = category.iloc[0]
        return f"<b>Cost driver:</b> <b>{row['cost_category']}</b> is the highest variance category at <b>${row['variance']:,.0f}</b>."

    if "saving" in q or "opportunity" in q:
        return f"<b>Savings opportunity:</b> Estimated savings opportunity is <b>${savings:,.0f}</b>. Start with high-risk categories and vendors with repeated variance."

    if "budget" in q or "variance" in q or "over" in q:
        return f"<b>Budget variance:</b> Actual spend is <b>${total_spend:,.0f}</b> versus budget of <b>${total_budget:,.0f}</b>, creating variance of <b>${variance:,.0f}</b>."

    return (
        f"<b>Summary:</b> Actual spend: <b>${total_spend:,.0f}</b>, budget: <b>${total_budget:,.0f}</b>, "
        f"variance: <b>${variance:,.0f}</b>, savings opportunity: <b>${savings:,.0f}</b>. "
        "Ask about vendors, departments, categories, savings, or variance."
    )


def answer_nexthire_question(question: str, score: int, matched: list[str], missing: list[str], ai_feedback: dict | None) -> str:
    """Simple rule-based assistant for NextHire results."""
    q = question.lower().strip()
    if not q:
        return "Ask a question such as: Why is this candidate a good fit?"

    if "score" in q or "fit" in q or "match" in q:
        return (
            f"<b>Match score:</b> The candidate scored <b>{score}/100</b>. "
            f"They match <b>{len(matched)}</b> role signals and are missing or weak on <b>{len(missing)}</b> signals."
        )

    if "missing" in q or "gap" in q or "weak" in q:
        gaps = ", ".join(missing[:12]) if missing else "No major missing keywords detected."
        return f"<b>Skill gaps:</b> {gaps}. Use these as screening questions or resume improvement areas."

    if "strength" in q or "strong" in q:
        strengths = ", ".join(matched[:12]) if matched else "No strong keyword matches detected."
        return f"<b>Candidate strengths:</b> {strengths}."

    if "question" in q or "interview" in q:
        if ai_feedback and ai_feedback.get("interview_questions"):
            questions = "<br>".join([f"{i+1}. {item}" for i, item in enumerate(ai_feedback["interview_questions"][:5])])
            return f"<b>Suggested interview questions:</b><br>{questions}"
        return (
            "<b>Suggested interview questions:</b><br>"
            "1. Tell me about a project where you analyzed business operations data.<br>"
            "2. How have you documented requirements for stakeholders?<br>"
            "3. What dashboard or reporting tools have you used?<br>"
            "4. How would you identify process improvement opportunities?<br>"
            "5. Which missing skills from this JD can you learn quickly?"
        )

    if "recommend" in q or "hire" in q:
        if score >= 75:
            return "<b>Recommendation:</b> Strong screen. Move forward if culture fit and role-specific experience are confirmed."
        if score >= 55:
            return "<b>Recommendation:</b> Possible screen. Validate missing skills and project depth in the interview."
        return "<b>Recommendation:</b> Weak match. Consider only if the role is flexible or training support is available."

    return (
        f"<b>Summary:</b> Score is <b>{score}/100</b>. Strong signals include: {', '.join(matched[:8]) or 'none detected'}. "
        f"Key gaps include: {', '.join(missing[:8]) or 'none detected'}."
    )


def generate_cost_executive_report(df: pd.DataFrame) -> str:
    """Generate a stronger executive CostOps report."""
    total_spend = df["actual_amount"].sum()
    total_budget = df["budget_amount"].sum()
    variance = total_spend - total_budget
    variance_pct = (variance / total_budget * 100) if total_budget else 0
    savings = df["savings_opportunity"].sum()

    top_dept = df.groupby("department")["variance"].sum().sort_values(ascending=False).head(3)
    top_vendor = df.groupby("vendor")["actual_amount"].sum().sort_values(ascending=False).head(3)
    top_category = df.groupby("cost_category")["variance"].sum().sort_values(ascending=False).head(3)
    high_risk_count = int((df["risk_level"] == "High").sum())

    return f"""OpsIntel AI - CostOps Executive Report

Executive Summary
Actual spend is ${total_spend:,.0f} against a budget of ${total_budget:,.0f}, creating a variance of ${variance:,.0f} ({variance_pct:.1f}%).
Estimated savings opportunity is ${savings:,.0f}. There are {high_risk_count} high-risk spend lines that should be reviewed first.

Top Budget Variance Departments
{chr(10).join([f"- {idx}: ${value:,.0f}" for idx, value in top_dept.items()])}

Highest Spend Vendors
{chr(10).join([f"- {idx}: ${value:,.0f}" for idx, value in top_vendor.items()])}

Top Cost Variance Categories
{chr(10).join([f"- {idx}: ${value:,.0f}" for idx, value in top_category.items()])}

Recommended 7-Day Action Plan
1. Review high-risk spend lines and confirm whether the variance is planned or avoidable.
2. Meet with owners of the top over-budget departments.
3. Review vendor concentration and identify renegotiation or consolidation opportunities.
4. Audit recurring SaaS, cloud, and services spend for unused or duplicated usage.
5. Set a recurring monthly variance alert threshold at 10%.

Business Impact
Reducing avoidable variance improves budget predictability, vendor accountability, and operating discipline.

Note
Savings are directional estimates based on reducing avoidable variance by 45%. Human review is recommended before business decisions.
"""


def generate_nexthire_executive_report(score: int, matched: list[str], missing: list[str], ai_feedback: dict | None) -> str:
    """Generate a stronger recruiter-ready NextHire report."""
    if score >= 75:
        recommendation = "Strong screen"
    elif score >= 55:
        recommendation = "Possible screen"
    else:
        recommendation = "Weak match"

    ai_summary = ""
    if ai_feedback:
        ai_summary = f"""
AI Hiring Summary
{ai_feedback.get("overall_feedback", "No AI summary available.")}

AI Strengths
{chr(10).join([f"- {item}" for item in ai_feedback.get("strengths", [])])}

AI Gaps / Risks
{chr(10).join([f"- {item}" for item in ai_feedback.get("gaps", [])])}

AI Interview Questions
{chr(10).join([f"{idx}. {item}" for idx, item in enumerate(ai_feedback.get("interview_questions", []), start=1)])}
"""

    return f"""OpsIntel AI - NextHire Executive Hiring Report

Recommendation
{recommendation}

Candidate-Role Match Score
{score}/100

Matched Role Signals
{chr(10).join([f"- {item}" for item in matched[:25]]) if matched else "- No strong matched signals detected."}

Missing / Weak Role Signals
{chr(10).join([f"- {item}" for item in missing[:25]]) if missing else "- No major missing signals detected."}

Recruiter Screening Guidance
1. Validate the candidate's strongest matched skills with specific project examples.
2. Ask about missing or weak role requirements directly.
3. Confirm business impact, stakeholder communication, and reporting experience.
4. Use the score as a screening aid, not as the final hiring decision.

Default Interview Questions
1. Tell me about a project where you analyzed operational or customer data.
2. How do you gather and document stakeholder requirements?
3. What dashboard or reporting tools have you used?
4. How do you explain findings to non-technical stakeholders?
5. Which missing skill from this role can you learn quickly?

{ai_summary}

Note
This report is AI-assisted and keyword-informed. Human recruiter review is required before hiring decisions.
"""

def render_supportops_page() -> None:
    """Render polished SupportOps Analyzer with product-first start experience."""
    render_module_header(
        "APPLICATION 1",
        "SupportOps Analyzer",
        "Upload support ticket data to detect SLA risk, escalation pressure, customer frustration, and manager-ready action priorities.",
    )

    intro_left, intro_right = st.columns([1.04, 0.96], gap="large")

    with intro_left:
        st.markdown(
            """
<div class="support-workflow-card">
  <div class="support-workflow-title">Support operations intelligence</div>
  <div class="support-workflow-copy">
    Move from raw ticket exports to a clean dashboard that shows SLA risk, escalation pressure,
    customer sentiment, agent workload, and next-best actions.
  </div>
  <div class="support-step-grid">
    <div class="support-step">
      <div class="support-step-num">1</div>
      <div class="support-step-title">Upload</div>
      <div class="support-step-copy">Bring your support ticket CSV.</div>
    </div>
    <div class="support-step">
      <div class="support-step-num">2</div>
      <div class="support-step-title">Validate</div>
      <div class="support-step-copy">Check fields and data quality.</div>
    </div>
    <div class="support-step">
      <div class="support-step-num">3</div>
      <div class="support-step-title">Analyze</div>
      <div class="support-step-copy">Find SLA, risk, and sentiment patterns.</div>
    </div>
    <div class="support-step">
      <div class="support-step-num">4</div>
      <div class="support-step-title">Act</div>
      <div class="support-step-copy">Export manager-ready actions.</div>
    </div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with intro_right:
        st.markdown(
            """
<div class="support-status-card">
  <div class="support-status-title">How this helps support teams</div>
  <div class="support-status-copy">
    • Spot SLA breach risk before escalation<br>
    • Identify frustrated customers and repeat contacts<br>
    • Find workload imbalance across agents<br>
    • Turn ticket patterns into manager actions<br>
    • Generate AI-assisted triage and reports
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
<div class="support-product-start">
  <div class="support-product-title">Analyze your support tickets</div>
  <div class="support-product-copy">
    Upload a support ticket CSV to see where customers are waiting, which teams are under pressure,
    and what actions can reduce SLA breaches and repeat work.
  </div>

  <div class="support-help-grid">
    <div class="support-help-card">
      <div class="support-help-icon">1</div>
      <div class="support-help-title">Find risky tickets</div>
      <div class="support-help-copy">Detect SLA pressure, escalation signals, and high-priority issues.</div>
    </div>
    <div class="support-help-card">
      <div class="support-help-icon">2</div>
      <div class="support-help-title">Understand patterns</div>
      <div class="support-help-copy">Break down risk by department, issue type, agent, and sentiment.</div>
    </div>
    <div class="support-help-card">
      <div class="support-help-icon">3</div>
      <div class="support-help-title">Create action plans</div>
      <div class="support-help-copy">Generate AI triage notes, daily briefings, and manager reports.</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="feature-pack-card">
  <div class="feature-pack-title">Need the right file format?</div>
  <div class="feature-pack-copy">
    Download the SupportOps CSV template, add your ticket data, then upload it below.
  </div>
  <div class="template-chip-row">
    <span class="template-chip">ticket_id</span>
    <span class="template-chip">department</span>
    <span class="template-chip">priority</span>
    <span class="template-chip">sla_breached</span>
    <span class="template-chip">sentiment</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.download_button(
        "Download SupportOps CSV Template",
        data=df_to_csv_bytes(get_support_template_df()),
        file_name="supportops_ticket_template.csv",
        mime="text/csv",
        width="stretch",
    )

    st.markdown(
        """
<div class="support-product-grid">
  <div class="support-upload-main">
    <div class="support-card-kicker">Primary workflow</div>
    <div class="support-card-title">Upload your support CSV</div>
    <div class="support-card-copy">
      Use real ticket data to analyze SLA risk, customer frustration, and operational bottlenecks.
    </div>
  </div>
  <div class="support-demo-side">
    <div class="support-demo-kicker">Optional demo</div>
    <div class="support-card-title">No file ready?</div>
    <div class="support-card-copy">
      Use the built-in sample dataset to preview the dashboard and AI workflow.
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    upload_col, demo_col = st.columns([1.25, 0.75], gap="large")
    with upload_col:
        uploaded_file = st.file_uploader(
            "Upload support ticket CSV",
            type=["csv"],
            help="Upload a CSV with support ticket fields.",
        )

    with demo_col:
        if st.button("Try demo data", width="stretch"):
            enable_support_demo()
        if st.button("Clear data", width="stretch"):
            st.session_state["support_demo_enabled"] = False
            st.rerun()

    with st.expander("View expected CSV format"):
        st.markdown(
            """
<div class="support-format-box">
  <div class="support-format-title">Recommended fields</div>
  <div class="support-card-copy">
    Your file should include these fields so the analyzer can calculate SLA risk, sentiment pressure, and agent workload.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="support-columns-grid">'
            + "".join([f'<span class="support-column-pill">{col}</span>' for col in REQUIRED_COLUMNS])
            + "</div>",
            unsafe_allow_html=True,
        )

    raw_df, data_source = get_support_data(uploaded_file)

    if raw_df is None:
        st.markdown(
            """
<div class="support-waiting-state">
  <div class="support-waiting-title">Waiting for support data</div>
  <div class="support-waiting-copy">
    Upload your CSV to run the real analysis. You can also click <b>Try demo data</b> to preview the workflow with sample tickets.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        return

    filtered_df, scored_df, column_check = prepare_support_analysis(raw_df)

    st.markdown(
        f"""
<div class="support-data-banner">
  <div>
    <div class="support-data-title">Dataset loaded successfully</div>
    <div class="support-data-sub">{data_source}</div>
  </div>
  <div class="support-data-pill">{len(raw_df):,} rows</div>
  <div class="support-data-pill">{len(raw_df.columns):,} columns</div>
</div>
""",
        unsafe_allow_html=True,
    )

    support_tabs = st.tabs(["Validate", "Overview", "SLA & Risk", "Agents", "Ask Data", "Report", "Raw Data"])

    with support_tabs[0]:
        st.subheader("Data Validation")
        st.markdown(
            """
<div class="support-tab-note">
  This section checks whether the loaded ticket data has the required fields and enough quality to support analysis.
</div>
""",
            unsafe_allow_html=True,
        )

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
            with st.expander("View required columns"):
                st.markdown(
                    '<div class="support-columns-grid">'
                    + "".join([f'<span class="support-column-pill">{col}</span>' for col in REQUIRED_COLUMNS])
                    + "</div>",
                    unsafe_allow_html=True,
                )
            st.stop()

        quality = data_quality_report(clean_support_ticket_data(raw_df))
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Quality Score", f"{quality['quality_score']}/100")
        q2.metric("Missing Values", quality["missing_value_total"])
        q3.metric("Duplicate IDs", quality["duplicate_ticket_count"])
        q4.metric("Invalid Dates", quality["invalid_date_count"])

        suggestions = support_quality_suggestions(quality, column_check)
        st.markdown('<div class="fix-card"><div class="fix-title">Data Quality Fix Suggestions</div><ul class="fix-list">', unsafe_allow_html=True)
        for suggestion in suggestions:
            st.markdown(f"<li>{suggestion}</li>", unsafe_allow_html=True)
        st.markdown("</ul></div>", unsafe_allow_html=True)

    with support_tabs[1]:
        st.subheader("Executive Summary")
        st.markdown(
            """
<div class="support-tab-note">
  A manager-ready view of volume, SLA health, escalation pressure, and customer sentiment.
</div>
""",
            unsafe_allow_html=True,
        )

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
        fig = px.bar(
            issue_summary,
            x="issue_type",
            y="total_tickets",
            title="Ticket Volume by Issue Type",
            text="total_tickets",
            color_discrete_sequence=["#3d3a8c"],
        )
        render_plotly_chart(fig)

    with support_tabs[2]:
        st.subheader("SLA & Escalation Risk")
        st.markdown(
            """
<div class="support-tab-note">
  This view highlights which departments and tickets need attention before they become expensive escalations.
</div>
""",
            unsafe_allow_html=True,
        )

        dept_sla = sla_summary_by_department(filtered_df)
        fig = px.bar(
            dept_sla,
            x="department",
            y="sla_breach_rate",
            title="SLA Breach Rate by Department",
            text="sla_breach_rate",
            color_discrete_sequence=["#3d3a8c"],
        )
        render_plotly_chart(fig)

        risk_counts = scored_df["risk_level"].value_counts().reset_index()
        risk_counts.columns = ["risk_level", "count"]
        fig = px.bar(
            risk_counts,
            x="risk_level",
            y="count",
            title="Escalation Risk Levels",
            text="count",
            color="risk_level",
            color_discrete_map={
                "Low": "#8faf9b",
                "Medium": "#9a7435",
                "High": "#9b4a4a",
            },
        )
        render_plotly_chart(fig)

        st.subheader("Top High-Risk Tickets")
        st.dataframe(top_high_risk_tickets(filtered_df), width="stretch")

    with support_tabs[3]:
        agent_subtabs = st.tabs(["AI Ticket Triage", "Daily Briefing", "Agent Performance"])

        with agent_subtabs[0]:
            st.subheader("AI Ticket Triage Agent")
            st.markdown(
                """
<div class="support-tab-note">
  Select a ticket and let the agent explain risk, urgency, routing, customer response, and manager action.
</div>
""",
                unsafe_allow_html=True,
            )

            ticket_options = scored_df["ticket_id"].tolist()
            selected_ticket_id = st.selectbox("Select a ticket", ticket_options)
            selected_ticket = scored_df[scored_df["ticket_id"] == selected_ticket_id].iloc[0]

            if st.button("Analyze Selected Ticket", width="stretch"):
                agent_result = analyze_ticket(selected_ticket)

                st.markdown('<div class="support-agent-result">', unsafe_allow_html=True)
                st.markdown('<div class="support-agent-title">Ticket triage result</div>', unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Risk Score", f"{agent_result['risk_score']}/100")
                col2.metric("Risk Level", agent_result["risk_level"])
                col3.metric("SLA Status", agent_result["sla_status"])
                col4.metric("Urgency", agent_result["urgency"])

                st.markdown(
                    f"""
<div class="support-agent-box">
  <b>Recommended Action:</b> {agent_result['recommended_action']}<br>
  <b>Routing:</b> {agent_result['routing_recommendation']}<br>
  <b>Business Impact:</b> {agent_result['business_impact']}
</div>
""",
                    unsafe_allow_html=True,
                )

                st.subheader("Customer Response Draft")
                st.write(agent_result["customer_response_draft"])

                st.subheader("Agent Trace")
                for step in agent_result["agent_trace"]:
                    st.write(f"✅ {step}")

                st.markdown("</div>", unsafe_allow_html=True)

        with agent_subtabs[1]:
            st.subheader("Daily SupportOps AI Briefing")
            st.markdown(
                """
<div class="support-tab-note">
  A manager-friendly daily briefing that summarizes risks, root causes, workload pressure, and recommended actions.
</div>
""",
                unsafe_allow_html=True,
            )

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

            st.subheader("Agent Trace")
            for step in briefing.get("agent_trace", []):
                st.write(f"✅ {step}")

        with agent_subtabs[2]:
            st.subheader("Agent Performance")
            st.markdown(
                """
<div class="support-tab-note">
  Compare agent workload and SLA breach rate to identify capacity or training issues.
</div>
""",
                unsafe_allow_html=True,
            )

            agent_summary = agent_performance_summary(filtered_df)
            fig = px.bar(
                agent_summary,
                x="agent",
                y="total_tickets",
                title="Ticket Workload by Agent",
                text="total_tickets",
                color_discrete_sequence=["#3d3a8c"],
            )
            render_plotly_chart(fig)

            fig = px.bar(
                agent_summary,
                x="agent",
                y="sla_breach_rate",
                title="SLA Breach Rate by Agent",
                text="sla_breach_rate",
                color_discrete_sequence=["#9a7435"],
            )
            render_plotly_chart(fig)
            st.dataframe(agent_summary, width="stretch")

    with support_tabs[4]:
        st.subheader("Ask Your Support Data")
        st.markdown(
            """
<div class="ask-card">
  <div class="ask-card-title">Ask OpsIntel about this support dataset</div>
  <div class="ask-card-copy">
    Ask about SLA risk, top departments, high-risk tickets, customer sentiment, or issue drivers.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        support_question = st.text_input(
            "Ask a support operations question",
            placeholder="Example: Which department has the highest SLA risk?",
            key="support_ask_question",
        )
        if support_question:
            answer = answer_support_question(support_question, scored_df)
            st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)

    with support_tabs[5]:
        st.markdown(
            """
<div class="support-report-card">
  <div class="support-report-title">Download SupportOps Report</div>
  <div class="support-report-copy">
    Export a manager briefing that summarizes the current support operation, risk signals, and recommended actions.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        report_text = generate_briefing_text(scored_df)
        st.text_area("Report Preview", report_text, height=360)
        st.download_button(
            "Download SupportOps Manager Report",
            data=report_text,
            file_name="supportops_manager_report.txt",
            mime="text/plain",
            width="stretch",
        )

    with support_tabs[6]:
        st.subheader("Raw Support Ticket Data")
        st.dataframe(scored_df, width="stretch")


def render_costops_page() -> None:
    """Render polished CostOps Analyzer."""
    render_module_header(
        "APPLICATION 2",
        "CostOps Analyzer",
        "Analyze spend, budget variance, vendor concentration, cost anomalies, and estimated savings opportunities.",
    )

    intro_left, intro_right = st.columns([1.04, 0.96], gap="large")

    with intro_left:
        st.markdown(
            """
<div class="costops-story-card">
  <div class="costops-title">Turn spend data into savings action</div>
  <div class="costops-copy">
    CostOps Analyzer reviews budget vs actual spend, department-level variance,
    vendor concentration, and avoidable overspend patterns. It is designed to help
    managers move from raw finance data to prioritized savings actions.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with intro_right:
        st.markdown(
            """
<div class="costops-signal-card">
  <div class="costops-title">What CostOps detects</div>
  <div class="costops-signal-list">
    <div class="costops-signal-row">
      <div class="costops-signal-icon">$</div>
      <div>
        <b>Budget variance</b>
        <p>Find where actual spend is exceeding planned spend.</p>
      </div>
    </div>
    <div class="costops-signal-row">
      <div class="costops-signal-icon">V</div>
      <div>
        <b>Vendor concentration</b>
        <p>Identify high-dependency vendors and spend concentration.</p>
      </div>
    </div>
    <div class="costops-signal-row">
      <div class="costops-signal-icon">!</div>
      <div>
        <b>Savings opportunities</b>
        <p>Estimate avoidable spend based on recurring variance patterns.</p>
      </div>
    </div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
<div class="costops-control-panel">
  <div class="costops-control-heading">Start cost analysis</div>
  <div class="costops-control-copy">
    Upload a cost CSV or use the built-in demo dataset. Required fields are:
    date, department, cost_category, vendor, budget_amount, and actual_amount.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="feature-pack-card">
  <div class="feature-pack-title">Need a CostOps upload template?</div>
  <div class="feature-pack-copy">
    Download the cost CSV template to structure budget, actual spend, vendor, owner, and department fields.
  </div>
  <div class="template-chip-row">
    <span class="template-chip">date</span>
    <span class="template-chip">department</span>
    <span class="template-chip">vendor</span>
    <span class="template-chip">budget_amount</span>
    <span class="template-chip">actual_amount</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.download_button(
        "Download CostOps CSV Template",
        data=df_to_csv_bytes(get_cost_template_df()),
        file_name="costops_spend_template.csv",
        mime="text/csv",
        width="stretch",
    )

    uploaded_file = st.file_uploader(
        "Upload cost CSV",
        type=["csv"],
        help="Optional. Use the demo data if you do not have a cost file.",
    )

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
        suggestions = cost_quality_suggestions(df, missing)
        st.markdown('<div class="fix-card"><div class="fix-title">Upload Fix Suggestions</div><ul class="fix-list">', unsafe_allow_html=True)
        for suggestion in suggestions:
            st.markdown(f"<li>{suggestion}</li>", unsafe_allow_html=True)
        st.markdown("</ul></div>", unsafe_allow_html=True)
        st.download_button(
            "Download Correct CostOps Template",
            data=df_to_csv_bytes(get_cost_template_df()),
            file_name="costops_spend_template.csv",
            mime="text/csv",
            width="stretch",
        )
        return

    df = analyze_cost_data(df)

    total_spend = df["actual_amount"].sum()
    total_budget = df["budget_amount"].sum()
    variance = total_spend - total_budget
    savings = df["savings_opportunity"].sum()

    st.markdown(
        f"""
<div class="costops-data-banner">
  <div>
    <div class="costops-data-title">Cost dataset loaded</div>
    <div class="costops-data-sub">{data_source}</div>
  </div>
  <div class="costops-data-pill">{len(df):,} rows</div>
  <div class="costops-data-pill">${savings:,.0f} estimated savings</div>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Actual Spend", f"${total_spend:,.0f}")
    c2.metric("Budget", f"${total_budget:,.0f}")
    c3.metric("Over Budget", f"${variance:,.0f}")
    c4.metric("Est. Savings Opportunity", f"${savings:,.0f}")

    tabs = st.tabs(["Spend Overview", "Departments & Vendors", "Ask Data", "Savings Report", "Raw Data"])

    with tabs[0]:
        st.subheader("Spend Overview")
        st.markdown(
            """
<div class="costops-tab-note">
  This view compares budgeted spend against actual spend and highlights categories creating the largest variance.
</div>
""",
            unsafe_allow_html=True,
        )

        monthly = df.groupby("date", as_index=False)[["budget_amount", "actual_amount"]].sum()
        fig = px.line(
            monthly,
            x="date",
            y=["budget_amount", "actual_amount"],
            title="Budget vs Actual Spend Trend",
            markers=True,
            color_discrete_sequence=["#8faf9b", "#3d3a8c"],
        )
        render_plotly_chart(fig)

        fig = px.bar(
            df,
            x="cost_category",
            y="variance",
            color="risk_level",
            title="Cost Variance by Category",
            text="variance",
            color_discrete_map={
                "Low": "#8faf9b",
                "Medium": "#9a7435",
                "High": "#9b4a4a",
            },
        )
        render_plotly_chart(fig)

    with tabs[1]:
        st.subheader("Departments & Vendors")
        st.markdown(
            """
<div class="costops-tab-note">
  Department and vendor views help identify where overspend is concentrated and where review should start.
</div>
""",
            unsafe_allow_html=True,
        )

        dept = df.groupby("department", as_index=False)[
            ["budget_amount", "actual_amount", "variance", "savings_opportunity"]
        ].sum()

        fig = px.bar(
            dept,
            x="department",
            y="variance",
            title="Budget Variance by Department",
            text="variance",
            color_discrete_sequence=["#9a7435"],
        )
        render_plotly_chart(fig)

        vendor = df.groupby("vendor", as_index=False)["actual_amount"].sum().sort_values(
            "actual_amount",
            ascending=False,
        )
        fig = px.pie(
            vendor,
            names="vendor",
            values="actual_amount",
            title="Vendor Spend Concentration",
            color_discrete_sequence=["#3d3a8c", "#8faf9b", "#9a7435", "#9b4a4a", "#6f6baa"],
        )
        render_plotly_chart(fig)

        st.dataframe(dept, width="stretch")

    with tabs[2]:
        st.subheader("Ask Your Cost Data")
        st.markdown(
            """
<div class="ask-card">
  <div class="ask-card-title">Ask OpsIntel about this spend dataset</div>
  <div class="ask-card-copy">
    Ask about vendors, departments, cost categories, budget variance, or savings opportunities.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        cost_question = st.text_input(
            "Ask a cost operations question",
            placeholder="Example: Which vendor is causing the most spend?",
            key="costops_ask_question",
        )
        if cost_question:
            answer = answer_cost_question(cost_question, df)
            st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.subheader("Savings Report")
        st.markdown(
            """
<div class="costops-report-card">
  <div class="costops-title">Manager-ready savings briefing</div>
  <div class="costops-copy">
    This report summarizes actual spend, budget variance, top risk areas, and recommended actions for finance or operations review.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        top_department = df.groupby("department")["variance"].sum().sort_values(ascending=False).index[0]
        top_vendor = df.groupby("vendor")["actual_amount"].sum().sort_values(ascending=False).index[0]

        st.markdown(
            f"""
<div class="costops-savings-grid">
  <div class="costops-savings-card">
    <div class="costops-savings-label">Estimated opportunity</div>
    <div class="costops-savings-value highlight">${savings:,.0f}</div>
  </div>
  <div class="costops-savings-card">
    <div class="costops-savings-label">Top overspending department</div>
    <div class="costops-savings-value">{top_department}</div>
  </div>
  <div class="costops-savings-card">
    <div class="costops-savings-label">Highest spend vendor</div>
    <div class="costops-savings-value">{top_vendor}</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        report = generate_cost_report(df)
        st.text_area("CostOps Report Preview", report, height=360)
        st.download_button(
            "Download CostOps Report",
            data=report,
            file_name="costops_savings_report.txt",
            mime="text/plain",
            width="stretch",
        )

    with tabs[4]:
        st.subheader("Raw Cost Data")
        st.markdown(
            """
<div class="costops-tab-note">
  Inspect the processed cost dataset including variance percentage, risk level, and estimated savings opportunity.
</div>
""",
            unsafe_allow_html=True,
        )
        st.dataframe(df, width="stretch")



def extract_uploaded_text(uploaded_file) -> tuple[str, str | None]:
    """Extract text from an uploaded resume or job description file.

    TXT, MD, and CSV work without extra dependencies.
    PDF and DOCX work if pypdf / python-docx are available in the environment.
    """
    if uploaded_file is None:
        return "", None

    file_name = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue()

    try:
        if file_name.endswith((".txt", ".md", ".csv")):
            return file_bytes.decode("utf-8", errors="ignore"), None

        if file_name.endswith(".pdf"):
            try:
                from pypdf import PdfReader
                import io

                reader = PdfReader(io.BytesIO(file_bytes))
                pages = []
                for page in reader.pages:
                    pages.append(page.extract_text() or "")
                extracted = "\n".join(pages).strip()
                if not extracted:
                    return "", "The PDF was uploaded, but no selectable text could be extracted. Try a text-based PDF or paste the content."
                return extracted, None
            except Exception:
                return "", "PDF upload needs the pypdf package. Add pypdf to requirements.txt, or upload TXT/MD/CSV, or paste the text."

        if file_name.endswith(".docx"):
            try:
                from docx import Document
                import io

                document = Document(io.BytesIO(file_bytes))
                extracted = "\n".join([p.text for p in document.paragraphs]).strip()
                if not extracted:
                    return "", "The DOCX was uploaded, but no text could be extracted. Try saving it as TXT or paste the content."
                return extracted, None
            except Exception:
                return "", "DOCX upload needs the python-docx package. Add python-docx to requirements.txt, or upload TXT/MD/CSV, or paste the text."

        return "", "Unsupported file type. Use TXT, MD, CSV, PDF, or DOCX."
    except Exception as exc:
        return "", f"Could not read uploaded file: {exc}"


def pick_uploaded_or_default(uploaded_file, default_text: str, label: str) -> str:
    """Use uploaded text when available; otherwise keep demo/default text."""
    extracted_text, error = extract_uploaded_text(uploaded_file)

    if error:
        st.warning(f"{label}: {error}")
        return default_text

    if extracted_text.strip():
        st.success(f"{label} uploaded and extracted successfully.")
        return extracted_text

    return default_text

def render_nexthire_page() -> None:
    """Render polished NextHire AI with upload options."""
    render_module_header(
        "APPLICATION 3",
        "NextHire AI",
        "Upload or paste candidate profiles and role requirements, then generate match scores, skill gaps, recruiter insights, and interview plans.",
    )

    intro_left, intro_right = st.columns([1.04, 0.96], gap="large")

    with intro_left:
        st.markdown(
            """
<div class="nexthire-story-card">
  <div class="nexthire-title">Turn candidate review into hiring intelligence</div>
  <div class="nexthire-copy">
    NextHire AI compares candidate profiles against role requirements, calculates a match score,
    identifies missing signals, and creates structured recruiter-ready hiring briefings.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with intro_right:
        st.markdown(
            """
<div class="nexthire-signal-card">
  <div class="nexthire-title">What NextHire AI reviews</div>
  <div class="nexthire-signal-list">
    <div class="nexthire-signal-row">
      <div class="nexthire-signal-icon">01</div>
      <div>
        <b>Role keyword coverage</b>
        <p>Compares candidate profile language against job requirements.</p>
      </div>
    </div>
    <div class="nexthire-signal-row">
      <div class="nexthire-signal-icon">02</div>
      <div>
        <b>Skill gaps and risks</b>
        <p>Highlights missing tools, responsibilities, or experience signals.</p>
      </div>
    </div>
    <div class="nexthire-signal-row">
      <div class="nexthire-signal-icon">03</div>
      <div>
        <b>Recruiter briefing</b>
        <p>Creates hiring summary, strengths, gaps, and interview questions.</p>
      </div>
    </div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
<div class="nexthire-control-panel">
  <div class="nexthire-control-heading">Candidate and role inputs</div>
  <div class="nexthire-control-copy">
    Upload a resume/profile and job description, or paste/edit the text directly below. Uploaded text automatically fills the editable boxes.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="nexthire-upload-grid">
  <div class="nexthire-upload-card">
    <div class="nexthire-upload-kicker">Candidate input</div>
    <div class="nexthire-upload-title">Upload resume or profile</div>
    <div class="nexthire-upload-copy">
      Upload TXT, MD, CSV, PDF, or DOCX. TXT/MD/CSV work directly; PDF/DOCX need parser packages in the environment.
    </div>
  </div>
  <div class="nexthire-upload-card">
    <div class="nexthire-upload-kicker">Role input</div>
    <div class="nexthire-upload-title">Upload job description</div>
    <div class="nexthire-upload-copy">
      Upload role requirements or paste them below. You can edit the extracted text before generating the briefing.
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="feature-pack-card">
  <div class="feature-pack-title">Want to test the workflow quickly?</div>
  <div class="feature-pack-copy">
    Download the sample candidate profile or sample job description, edit them, and upload them back into NextHire AI.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    sample_cols = st.columns(2)
    with sample_cols[0]:
        st.download_button(
            "Download Sample Candidate Profile",
            data=DEMO_RESUME.encode("utf-8"),
            file_name="sample_candidate_profile.txt",
            mime="text/plain",
            width="stretch",
        )
    with sample_cols[1]:
        st.download_button(
            "Download Sample Job Description",
            data=DEMO_JD.encode("utf-8"),
            file_name="sample_job_description.txt",
            mime="text/plain",
            width="stretch",
        )

    upload_cols = st.columns(2)
    with upload_cols[0]:
        resume_upload = st.file_uploader(
            "Upload candidate resume/profile",
            type=["txt", "md", "csv", "pdf", "docx"],
            key="nexthire_resume_upload",
        )
    with upload_cols[1]:
        jd_upload = st.file_uploader(
            "Upload job description/role requirements",
            type=["txt", "md", "csv", "pdf", "docx"],
            key="nexthire_jd_upload",
        )

    resume_default = pick_uploaded_or_default(resume_upload, DEMO_RESUME, "Candidate file")
    jd_default = pick_uploaded_or_default(jd_upload, DEMO_JD, "Role file")

    st.markdown(
        """
<div class="nexthire-input-note">
  <b>Tip:</b> Uploading fills the box, but the text remains editable. This makes it easy to clean formatting, remove irrelevant sections, or test different role requirements.
</div>
""",
        unsafe_allow_html=True,
    )

    input_cols = st.columns(2)
    with input_cols[0]:
        resume_text = st.text_area("Candidate resume / profile", value=resume_default, height=330)
    with input_cols[1]:
        jd_text = st.text_area("Role requirements / job description", value=jd_default, height=330)

    if not resume_text.strip() or not jd_text.strip():
        st.warning("Add both a candidate profile and role requirements to analyze.")
        return

    score, matched, missing = analyze_resume_match(resume_text, jd_text)

    if "nexthire_ai_feedback" not in st.session_state:
        st.session_state["nexthire_ai_feedback"] = None

    st.markdown(
        """
<div class="nexthire-ai-panel">
  <div class="nexthire-ai-status">Gemini briefing available</div>
  <div class="nexthire-title">Generate recruiter decision support</div>
  <div class="nexthire-copy">
    Run the AI briefing to generate a hiring summary, strengths, gaps, recruiter recommendations, and interview questions.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.button("Generate Gemini Hiring Briefing", width="stretch"):
        with st.spinner("Gemini is analyzing the candidate profile and role requirements..."):
            st.session_state["nexthire_ai_feedback"] = generate_nexthire_ai_feedback(
                resume_text,
                jd_text,
                score,
                matched,
                missing,
            )

    ai_feedback = st.session_state.get("nexthire_ai_feedback")

    st.markdown(
        f"""
<div class="nexthire-score-strip">
  <div class="nexthire-score-card primary">
    <div class="nexthire-score-label">Candidate-role match score</div>
    <div class="nexthire-score-value highlight">{score}/100</div>
  </div>
  <div class="nexthire-score-card">
    <div class="nexthire-score-label">Matched keywords</div>
    <div class="nexthire-score-value">{len(matched)}</div>
  </div>
  <div class="nexthire-score-card">
    <div class="nexthire-score-label">Missing keywords</div>
    <div class="nexthire-score-value">{len(missing)}</div>
  </div>
  <div class="nexthire-score-card">
    <div class="nexthire-score-label">Briefing status</div>
    <div class="nexthire-score-value">{"Ready" if ai_feedback else "Pending"}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Candidate Match", "Recruiter Insights", "Ask Match", "Interview Plan", "Hiring Report"])

    with tabs[0]:
        st.subheader("Candidate Match")
        st.markdown(
            """
<div class="nexthire-tab-note">
  This view compares the candidate profile against role requirements using keyword coverage and gap detection.
</div>
""",
            unsafe_allow_html=True,
        )

        matched_html = "".join([f'<span class="keyword-pill good">{item}</span>' for item in matched[:30]]) or '<span class="keyword-pill">No strong matches found</span>'
        missing_html = "".join([f'<span class="keyword-pill gap">{item}</span>' for item in missing[:30]]) or '<span class="keyword-pill">No major missing keywords found</span>'

        st.markdown(
            f"""
<div class="nexthire-keyword-grid">
  <div class="nexthire-keyword-card">
    <div class="nexthire-keyword-title">Matched Role Keywords</div>
    <div class="keyword-pill-wrap">{matched_html}</div>
  </div>
  <div class="nexthire-keyword-card">
    <div class="nexthire-keyword-title">Missing / Weak Role Keywords</div>
    <div class="keyword-pill-wrap">{missing_html}</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        chart_df = pd.DataFrame(
            {
                "category": ["Matched", "Missing"],
                "count": [len(matched), len(missing)],
            }
        )
        fig = px.bar(
            chart_df,
            x="category",
            y="count",
            title="Candidate-Role Keyword Coverage",
            text="count",
            color="category",
            color_discrete_map={
                "Matched": "#8faf9b",
                "Missing": "#9b4a4a",
            },
        )
        render_plotly_chart(fig)

    with tabs[1]:
        st.subheader("Recruiter Insights")
        st.markdown(
            """
<div class="nexthire-tab-note">
  Gemini generates recruiter-facing decision support. If Gemini is unavailable, the module falls back to keyword-based hiring guidance.
</div>
""",
            unsafe_allow_html=True,
        )

        if ai_feedback:
            st.markdown(
                f"""
<div class="nexthire-list-card">
  <div class="nexthire-list-title">Hiring Summary</div>
  <div class="nexthire-copy">{ai_feedback.get("overall_feedback", "No hiring summary available.")}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            st.markdown('<div class="nexthire-list-card"><div class="nexthire-list-title">Candidate Strengths</div>', unsafe_allow_html=True)
            for item in ai_feedback.get("strengths", []):
                st.write(f"✅ {item}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="nexthire-list-card"><div class="nexthire-list-title">Hiring Gaps / Risks</div>', unsafe_allow_html=True)
            for item in ai_feedback.get("gaps", []):
                st.write(f"⚠️ {item}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="nexthire-list-card"><div class="nexthire-list-title">Recruiter Recommendations</div>', unsafe_allow_html=True)
            for idx, suggestion in enumerate(ai_feedback.get("resume_improvements", []), start=1):
                st.write(f"{idx}. {suggestion}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("### Agent Trace")
            for step in ai_feedback.get("agent_trace", []):
                st.write(f"✅ {step}")
        else:
            st.info("Click **Generate Gemini Hiring Briefing** above to get AI-powered recruiter insights.")

    with tabs[2]:
        st.subheader("Ask About This Match")
        st.markdown(
            """
<div class="ask-card">
  <div class="ask-card-title">Ask OpsIntel about the candidate-role match</div>
  <div class="ask-card-copy">
    Ask about fit, gaps, strengths, hiring recommendation, or interview questions.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        match_question = st.text_input(
            "Ask a hiring question",
            placeholder="Example: What are the biggest gaps for this candidate?",
            key="nexthire_ask_question",
        )
        if match_question:
            answer = answer_nexthire_question(match_question, score, matched, missing, ai_feedback)
            st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.subheader("Structured Interview Plan")
        st.markdown(
            """
<div class="nexthire-tab-note">
  Use these questions to validate experience, business impact, stakeholder communication, and missing role requirements.
</div>
""",
            unsafe_allow_html=True,
        )

        if ai_feedback:
            questions = ai_feedback.get("interview_questions", [])
            if questions:
                for idx, question in enumerate(questions, start=1):
                    st.write(f"{idx}. {question}")
            else:
                st.info("No interview questions were generated.")
        else:
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

    with tabs[4]:
        st.markdown(
            """
<div class="nexthire-report-card">
  <div class="nexthire-title">Download hiring report</div>
  <div class="nexthire-copy">
    Export a recruiter-ready report with match score, strengths, gaps, recommendations, and interview questions.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        if ai_feedback:
            report = generate_nexthire_executive_report(score, matched, missing, ai_feedback)
            legacy_report = f"""OpsIntel AI - NextHire Gemini Hiring Report

Candidate-Role Match Score: {score}/100

Hiring Summary:
{ai_feedback.get("overall_feedback", "No hiring summary available.")}

Candidate Strengths:
{chr(10).join([f"- {item}" for item in ai_feedback.get("strengths", [])])}

Hiring Gaps / Risks:
{chr(10).join([f"- {item}" for item in ai_feedback.get("gaps", [])])}

Recruiter Recommendations:
{chr(10).join([f"{idx}. {item}" for idx, item in enumerate(ai_feedback.get("resume_improvements", []), start=1)])}

Structured Interview Questions:
{chr(10).join([f"{idx}. {item}" for idx, item in enumerate(ai_feedback.get("interview_questions", []), start=1)])}

Agent Trace:
{chr(10).join([f"- {item}" for item in ai_feedback.get("agent_trace", [])])}
"""
        else:
            report = generate_nexthire_executive_report(score, matched, missing, ai_feedback)

        st.text_area("Hiring Report Preview", report, height=420)
        st.download_button(
            "Download NextHire Hiring Report",
            data=report,
            file_name="nexthire_hiring_report.txt",
            mime="text/plain",
            width="stretch",
        )




# =============================================================================
# PROCESSOPS ANALYZER HELPERS
# =============================================================================
PROCESSOPS_REQUIRED_COLUMNS = [
    "case_id",
    "process_name",
    "step_name",
    "owner",
    "department",
    "start_time",
    "end_time",
    "status",
    "rework_flag",
    "approval_required",
    "automation_candidate",
]


def get_processops_template_df() -> pd.DataFrame:
    """Return a downloadable ProcessOps CSV template."""
    return pd.DataFrame(
        [
            {
                "case_id": "PR-1001",
                "process_name": "Purchase Request",
                "step_name": "Manager Approval",
                "owner": "Anita",
                "department": "Operations",
                "start_time": "2026-06-01 09:00:00",
                "end_time": "2026-06-02 13:30:00",
                "status": "Completed",
                "rework_flag": "No",
                "approval_required": "Yes",
                "automation_candidate": "No",
                "notes": "Waiting for approval queue",
            },
            {
                "case_id": "PR-1002",
                "process_name": "Expense Reimbursement",
                "step_name": "Receipt Validation",
                "owner": "Jeremiah",
                "department": "Finance",
                "start_time": "2026-06-01 10:15:00",
                "end_time": "2026-06-01 18:45:00",
                "status": "Reworked",
                "rework_flag": "Yes",
                "approval_required": "Yes",
                "automation_candidate": "Yes",
                "notes": "Manual data entry error",
            },
        ]
    )


@st.cache_data
def load_processops_demo_data() -> pd.DataFrame:
    """Create demo process log data."""
    rows = [
        ["PR-1001", "Purchase Request", "Request Intake", "Kim", "Operations", "2026-06-01 09:00", "2026-06-01 10:15", "Completed", "No", "No", "Yes", "Manual form intake"],
        ["PR-1001", "Purchase Request", "Manager Approval", "Anita", "Operations", "2026-06-01 10:20", "2026-06-02 13:30", "Completed", "No", "Yes", "No", "Approval queue delay"],
        ["PR-1001", "Purchase Request", "Finance Review", "Jeremiah", "Finance", "2026-06-02 14:00", "2026-06-03 11:30", "Completed", "No", "Yes", "Yes", "Manual validation"],
        ["PR-1002", "Expense Reimbursement", "Expense Entry", "Maya", "Customer Service", "2026-06-01 08:30", "2026-06-01 09:10", "Completed", "No", "No", "Yes", "Manual receipt entry"],
        ["PR-1002", "Expense Reimbursement", "Receipt Validation", "Jeremiah", "Finance", "2026-06-01 09:15", "2026-06-02 17:20", "Reworked", "Yes", "Yes", "Yes", "Incorrect receipt amount"],
        ["PR-1002", "Expense Reimbursement", "Final Approval", "Anita", "Customer Service", "2026-06-03 09:00", "2026-06-04 15:00", "Completed", "No", "Yes", "No", "Manager unavailable"],
        ["ON-2001", "Customer Onboarding", "Account Setup", "Ravi", "Implementation", "2026-06-01 11:00", "2026-06-01 15:00", "Completed", "No", "No", "Yes", "Repeat setup tasks"],
        ["ON-2001", "Customer Onboarding", "Document Collection", "Kim", "Implementation", "2026-06-01 15:15", "2026-06-04 16:00", "Blocked", "No", "No", "No", "Waiting on customer documents"],
        ["ON-2002", "Customer Onboarding", "Account Setup", "Ravi", "Implementation", "2026-06-02 09:00", "2026-06-02 12:30", "Completed", "No", "No", "Yes", "Standard setup"],
        ["ON-2002", "Customer Onboarding", "Training Scheduling", "Maya", "Implementation", "2026-06-02 13:00", "2026-06-05 10:00", "Delayed", "No", "No", "Yes", "Manual scheduling coordination"],
        ["HR-3001", "Hiring Approval", "Role Intake", "Anita", "HR", "2026-06-01 09:00", "2026-06-01 11:00", "Completed", "No", "No", "Yes", "Standard intake"],
        ["HR-3001", "Hiring Approval", "Budget Approval", "Jeremiah", "Finance", "2026-06-01 11:30", "2026-06-04 12:00", "Delayed", "No", "Yes", "No", "Budget owner review delay"],
        ["HR-3001", "Hiring Approval", "Recruiter Assignment", "Maya", "HR", "2026-06-04 13:00", "2026-06-04 16:30", "Completed", "No", "No", "Yes", "Manual routing"],
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "case_id",
            "process_name",
            "step_name",
            "owner",
            "department",
            "start_time",
            "end_time",
            "status",
            "rework_flag",
            "approval_required",
            "automation_candidate",
            "notes",
        ],
    )


def clean_processops_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich process log data."""
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]

    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df["end_time"] = pd.to_datetime(df["end_time"], errors="coerce")
    df["cycle_hours"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 3600
    df["cycle_hours"] = df["cycle_hours"].fillna(0).clip(lower=0)

    for col in ["rework_flag", "approval_required", "automation_candidate"]:
        df[col] = df[col].astype(str).str.strip().str.title()

    df["is_rework"] = df["rework_flag"].isin(["Yes", "True", "1"])
    df["needs_approval"] = df["approval_required"].isin(["Yes", "True", "1"])
    df["is_automation_candidate"] = df["automation_candidate"].isin(["Yes", "True", "1"])
    df["is_delayed_or_blocked"] = df["status"].astype(str).str.lower().isin(["delayed", "blocked", "reworked"])

    df["bottleneck_score"] = (
        (df["cycle_hours"] * 2)
        + (df["is_rework"].astype(int) * 20)
        + (df["needs_approval"].astype(int) * 10)
        + (df["is_delayed_or_blocked"].astype(int) * 18)
        + (df["is_automation_candidate"].astype(int) * 6)
    ).round(1)

    df["risk_level"] = pd.cut(
        df["bottleneck_score"],
        bins=[-1, 18, 45, 10**9],
        labels=["Low", "Medium", "High"],
    ).astype(str)

    return df


def validate_processops_columns(df: pd.DataFrame) -> dict:
    """Validate ProcessOps columns."""
    cols = set([str(col).strip().lower() for col in df.columns])
    missing = [col for col in PROCESSOPS_REQUIRED_COLUMNS if col not in cols]
    return {"passed": len(missing) == 0, "missing_columns": missing}


def calculate_processops_kpis(df: pd.DataFrame) -> dict:
    """Calculate ProcessOps KPIs."""
    total_cases = df["case_id"].nunique()
    total_steps = len(df)
    avg_cycle = df["cycle_hours"].mean() if total_steps else 0
    rework_rate = df["is_rework"].mean() * 100 if total_steps else 0
    approval_delay = df[df["needs_approval"]]["cycle_hours"].mean() if df["needs_approval"].any() else 0
    automation_opps = int(df["is_automation_candidate"].sum())
    high_risk_steps = int((df["risk_level"] == "High").sum())

    return {
        "total_cases": total_cases,
        "total_steps": total_steps,
        "avg_cycle_hours": round(avg_cycle, 1),
        "rework_rate": round(rework_rate, 1),
        "approval_delay_hours": round(approval_delay, 1),
        "automation_opps": automation_opps,
        "high_risk_steps": high_risk_steps,
    }


def process_step_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize process steps."""
    return (
        df.groupby(["process_name", "step_name"], as_index=False)
        .agg(
            total_steps=("case_id", "count"),
            avg_cycle_hours=("cycle_hours", "mean"),
            rework_count=("is_rework", "sum"),
            delayed_or_blocked=("is_delayed_or_blocked", "sum"),
            automation_opportunities=("is_automation_candidate", "sum"),
            avg_bottleneck_score=("bottleneck_score", "mean"),
        )
        .round(1)
        .sort_values("avg_bottleneck_score", ascending=False)
    )


def process_owner_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize workload by owner."""
    return (
        df.groupby(["owner", "department"], as_index=False)
        .agg(
            assigned_steps=("case_id", "count"),
            avg_cycle_hours=("cycle_hours", "mean"),
            rework_count=("is_rework", "sum"),
            high_risk_steps=("risk_level", lambda x: int((x == "High").sum())),
        )
        .round(1)
        .sort_values("assigned_steps", ascending=False)
    )


def process_quality_suggestions(df: pd.DataFrame, column_check: dict) -> list[str]:
    """Generate ProcessOps upload fix suggestions."""
    suggestions = []

    if not column_check.get("passed", False):
        suggestions.append(f"Add missing required columns: {', '.join(column_check.get('missing_columns', []))}.")

    invalid_start = df["start_time"].isna().sum() if "start_time" in df.columns else 0
    invalid_end = df["end_time"].isna().sum() if "end_time" in df.columns else 0
    if invalid_start or invalid_end:
        suggestions.append("Fix invalid start_time or end_time values. Use YYYY-MM-DD HH:MM format.")

    if "case_id" in df.columns and df["case_id"].isna().sum() > 0:
        suggestions.append("Fill missing case_id values so each process instance can be tracked end-to-end.")

    if not suggestions:
        suggestions.append("Process data looks analysis-ready. Review bottlenecks, approval delays, and automation opportunities.")

    return suggestions


def answer_process_question(question: str, df: pd.DataFrame) -> str:
    """Simple rule-based assistant for ProcessOps data."""
    q = question.lower().strip()
    if not q:
        return "Ask a question such as: Which step is the biggest bottleneck?"

    kpis = calculate_processops_kpis(df)
    steps = process_step_summary(df)
    owners = process_owner_summary(df)

    top_step = steps.iloc[0]
    top_owner = owners.iloc[0]

    if "bottleneck" in q or "slow" in q or "delay" in q:
        return (
            f"<b>Biggest bottleneck:</b> <b>{top_step['step_name']}</b> in "
            f"<b>{top_step['process_name']}</b> has the highest average bottleneck score "
            f"({top_step['avg_bottleneck_score']}). Average cycle time is "
            f"<b>{top_step['avg_cycle_hours']} hours</b>."
        )

    if "approval" in q:
        return (
            f"<b>Approval delay:</b> Steps requiring approval average "
            f"<b>{kpis['approval_delay_hours']} hours</b>. Review manager approval and finance review steps first."
        )

    if "rework" in q:
        return (
            f"<b>Rework:</b> Rework rate is <b>{kpis['rework_rate']}%</b>. "
            "Look for manual entry, missing documentation, and validation steps with repeated corrections."
        )

    if "automation" in q or "automate" in q:
        return (
            f"<b>Automation opportunity:</b> There are <b>{kpis['automation_opps']}</b> automation candidate steps. "
            "Start with repetitive intake, validation, routing, and scheduling tasks."
        )

    if "owner" in q or "workload" in q:
        return (
            f"<b>Owner workload:</b> <b>{top_owner['owner']}</b> has the highest assigned step count "
            f"({top_owner['assigned_steps']}). Review workload balance and handoff delays."
        )

    return (
        f"<b>Process summary:</b> {kpis['total_cases']} cases, {kpis['total_steps']} steps, "
        f"average cycle time {kpis['avg_cycle_hours']} hours, rework rate {kpis['rework_rate']}%, "
        f"and {kpis['high_risk_steps']} high-risk steps."
    )


def generate_processops_report(df: pd.DataFrame) -> str:
    """Generate ProcessOps executive report."""
    kpis = calculate_processops_kpis(df)
    steps = process_step_summary(df).head(5)
    owners = process_owner_summary(df).head(5)

    return f"""OpsIntel AI - ProcessOps Executive Improvement Report

Executive Summary
The process dataset includes {kpis['total_cases']} cases and {kpis['total_steps']} workflow steps.
Average cycle time is {kpis['avg_cycle_hours']} hours, rework rate is {kpis['rework_rate']}%, and there are {kpis['high_risk_steps']} high-risk process steps.

Key Process Risks
- Average approval step delay: {kpis['approval_delay_hours']} hours
- Automation candidate steps: {kpis['automation_opps']}
- High-risk steps: {kpis['high_risk_steps']}

Top Bottleneck Steps
{chr(10).join([f"- {row.process_name} / {row.step_name}: {row.avg_cycle_hours} hrs avg, score {row.avg_bottleneck_score}" for row in steps.itertuples()])}

Owner Workload Hotspots
{chr(10).join([f"- {row.owner} ({row.department}): {row.assigned_steps} steps, {row.high_risk_steps} high-risk" for row in owners.itertuples()])}

Recommended Improvement Actions
1. Review the top bottleneck step and identify why cycle time is high.
2. Reduce unnecessary approval layers for low-risk requests.
3. Automate repetitive intake, validation, routing, and scheduling steps.
4. Create a standard operating procedure for reworked steps.
5. Add weekly monitoring for cycle time, rework, and blocked cases.

Business Impact
Improving process flow can reduce waiting time, manual rework, approval delays, and operational frustration.

Note
This is a portfolio demo report. Human review is recommended before business decisions.
"""


def render_processops_page() -> None:
    """Render ProcessOps Analyzer."""
    render_module_header(
        "APPLICATION 4",
        "ProcessOps Analyzer",
        "Upload process logs to identify bottlenecks, approval delays, rework, manual handoffs, and automation opportunities.",
    )

    intro_left, intro_right = st.columns([1.04, 0.96], gap="large")
    with intro_left:
        st.markdown(
            """
<div class="processops-story-card">
  <div class="processops-title">Turn messy process logs into improvement actions</div>
  <div class="processops-copy">
    ProcessOps Analyzer helps business analysts and operations teams find where work gets stuck,
    where approvals slow down, and which manual steps are ready for automation.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    with intro_right:
        st.markdown(
            """
<div class="processops-signal-card">
  <div class="processops-title">What ProcessOps detects</div>
  <div class="processops-signal-list">
    <div class="processops-signal-row">
      <div class="processops-signal-icon">01</div>
      <div>
        <b>Bottlenecks</b>
        <p>Find slow process steps and blocked handoffs.</p>
      </div>
    </div>
    <div class="processops-signal-row">
      <div class="processops-signal-icon">02</div>
      <div>
        <b>Rework</b>
        <p>Detect repeated corrections, validation failures, and manual mistakes.</p>
      </div>
    </div>
    <div class="processops-signal-row">
      <div class="processops-signal-icon">03</div>
      <div>
        <b>Automation opportunities</b>
        <p>Prioritize repetitive steps that can be automated or simplified.</p>
      </div>
    </div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown(
        """
<div class="processops-start-card">
  <div class="processops-title">Analyze a business process</div>
  <div class="processops-copy">
    Upload a process log CSV or try the demo dataset. This works for approval flows, onboarding,
    expense reimbursement, purchase requests, hiring approvals, and other repeated business processes.
  </div>
  <div class="processops-help-grid">
    <div class="processops-help-card">
      <div class="processops-help-num">1</div>
      <div class="processops-help-title">Map the process</div>
      <div class="processops-help-copy">Track case IDs, steps, owners, and departments.</div>
    </div>
    <div class="processops-help-card">
      <div class="processops-help-num">2</div>
      <div class="processops-help-title">Find delays</div>
      <div class="processops-help-copy">Compare cycle time across steps and approvals.</div>
    </div>
    <div class="processops-help-card">
      <div class="processops-help-num">3</div>
      <div class="processops-help-title">Spot rework</div>
      <div class="processops-help-copy">Flag repeated corrections and manual errors.</div>
    </div>
    <div class="processops-help-card">
      <div class="processops-help-num">4</div>
      <div class="processops-help-title">Improve flow</div>
      <div class="processops-help-copy">Generate SOP, automation, and action recommendations.</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="processops-template-card">
  <div class="processops-title">Need a process log template?</div>
  <div class="processops-copy">
    Download the template, fill in your process steps, and upload it for bottleneck analysis.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.download_button(
        "Download ProcessOps CSV Template",
        data=df_to_csv_bytes(get_processops_template_df()),
        file_name="processops_process_log_template.csv",
        mime="text/csv",
        width="stretch",
    )

    upload_col, demo_col = st.columns([1.25, 0.75], gap="large")
    with upload_col:
        uploaded_file = st.file_uploader(
            "Upload process log CSV",
            type=["csv"],
            help="Upload a process log CSV with case, step, owner, start time, end time, and status fields.",
            key="processops_upload",
        )

    with demo_col:
        if st.button("Try demo process data", width="stretch"):
            enable_process_demo()
        if st.button("Clear ProcessOps data", width="stretch"):
            st.session_state["process_demo_enabled"] = False
            st.rerun()

    if uploaded_file is not None:
        raw_df = pd.read_csv(uploaded_file)
        data_source = f"Uploaded file: {uploaded_file.name}"
    elif st.session_state.get("process_demo_enabled", False):
        raw_df = load_processops_demo_data()
        data_source = "Demo process dataset"
    else:
        st.markdown(
            """
<div class="processops-start-card">
  <div class="processops-title">Open the ProcessOps workflow</div>
  <div class="processops-copy">
    Upload a process log CSV or click <b>Try demo process data</b> to open the full dashboard with KPIs, bottlenecks,
    automation opportunities, ask-data assistant, and executive improvement report.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        return

    column_check = validate_processops_columns(raw_df)
    if not column_check["passed"]:
        st.error(f"Missing required columns: {column_check['missing_columns']}")
        st.download_button(
            "Download Correct ProcessOps Template",
            data=df_to_csv_bytes(get_processops_template_df()),
            file_name="processops_process_log_template.csv",
            mime="text/csv",
            width="stretch",
        )
        return

    df = clean_processops_data(raw_df)
    kpis = calculate_processops_kpis(df)

    st.markdown(
        f"""
<div class="processops-data-banner">
  <div>
    <div class="processops-data-title">Process data loaded</div>
    <div class="processops-data-sub">{data_source}</div>
  </div>
  <div class="processops-data-pill">{kpis['total_cases']:,} cases</div>
  <div class="processops-data-pill">{kpis['total_steps']:,} steps</div>
</div>
""",
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Overview", "Bottlenecks", "Automation", "Ask Data", "Report", "Raw Data"])

    with tabs[0]:
        st.subheader("Process Health Overview")
        st.markdown(
            """
<div class="processops-tab-note">
  A business analyst view of cycle time, approval delay, rework, automation opportunities, and high-risk process steps.
</div>
""",
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Cases", f"{kpis['total_cases']:,}")
        c2.metric("Avg Cycle Time", f"{kpis['avg_cycle_hours']} hrs")
        c3.metric("Rework Rate", f"{kpis['rework_rate']}%")
        c4.metric("High-Risk Steps", f"{kpis['high_risk_steps']:,}")

        c5, c6 = st.columns(2)
        c5.metric("Approval Delay Avg", f"{kpis['approval_delay_hours']} hrs")
        c6.metric("Automation Candidates", f"{kpis['automation_opps']:,}")

        process_summary = (
            df.groupby("process_name", as_index=False)
            .agg(avg_cycle_hours=("cycle_hours", "mean"), steps=("case_id", "count"))
            .round(1)
        )
        fig = px.bar(
            process_summary,
            x="process_name",
            y="avg_cycle_hours",
            title="Average Cycle Time by Process",
            text="avg_cycle_hours",
            color_discrete_sequence=["#3d3a8c"],
        )
        render_plotly_chart(fig)

    with tabs[1]:
        st.subheader("Bottleneck Analysis")
        st.markdown(
            """
<div class="processops-tab-note">
  Find process steps with high cycle time, rework, delayed status, approval pressure, and high bottleneck scores.
</div>
""",
            unsafe_allow_html=True,
        )

        step_summary = process_step_summary(df)
        fig = px.bar(
            step_summary.head(10),
            x="step_name",
            y="avg_bottleneck_score",
            color="process_name",
            title="Top Bottleneck Steps",
            text="avg_bottleneck_score",
            color_discrete_sequence=["#3d3a8c", "#8faf9b", "#9a7435", "#9b4a4a"],
        )
        render_plotly_chart(fig)

        st.dataframe(step_summary, width="stretch")

    with tabs[2]:
        st.subheader("Automation & Rework Opportunities")
        st.markdown(
            """
<div class="processops-tab-note">
  Prioritize repetitive, manual, reworked, and delayed steps for SOP improvement or lightweight automation.
</div>
""",
            unsafe_allow_html=True,
        )

        automation_df = df[df["is_automation_candidate"]].copy()
        rework_df = df[df["is_rework"]].copy()

        st.markdown(
            f"""
<div class="processops-opportunity-grid">
  <div class="processops-opportunity-card">
    <div class="processops-opportunity-label">Automation candidates</div>
    <div class="processops-opportunity-value highlight">{len(automation_df):,}</div>
  </div>
  <div class="processops-opportunity-card">
    <div class="processops-opportunity-label">Rework steps</div>
    <div class="processops-opportunity-value">{len(rework_df):,}</div>
  </div>
  <div class="processops-opportunity-card">
    <div class="processops-opportunity-label">Delayed / blocked / reworked</div>
    <div class="processops-opportunity-value">{int(df['is_delayed_or_blocked'].sum()):,}</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        owner_summary = process_owner_summary(df)
        fig = px.bar(
            owner_summary,
            x="owner",
            y="assigned_steps",
            color="department",
            title="Workload by Process Owner",
            text="assigned_steps",
            color_discrete_sequence=["#3d3a8c", "#8faf9b", "#9a7435", "#9b4a4a"],
        )
        render_plotly_chart(fig)

        st.subheader("Automation Candidate Steps")
        st.dataframe(automation_df, width="stretch")

    with tabs[3]:
        st.subheader("Ask Your Process Data")
        st.markdown(
            """
<div class="ask-card">
  <div class="ask-card-title">Ask OpsIntel about this process dataset</div>
  <div class="ask-card-copy">
    Ask about bottlenecks, approval delays, rework, automation opportunities, owners, or workload.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        question = st.text_input(
            "Ask a process improvement question",
            placeholder="Example: Which step is the biggest bottleneck?",
            key="processops_ask_question",
        )
        if question:
            answer = answer_process_question(question, df)
            st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)

    with tabs[4]:
        st.markdown(
            """
<div class="processops-report-card">
  <div class="processops-title">Download ProcessOps Improvement Report</div>
  <div class="processops-copy">
    Export a business analyst style report with bottlenecks, owner workload, rework, automation opportunities, and recommended actions.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        suggestions = process_quality_suggestions(df, column_check)
        st.markdown('<div class="fix-card"><div class="fix-title">Data Quality & Process Fix Suggestions</div><ul class="fix-list">', unsafe_allow_html=True)
        for suggestion in suggestions:
            st.markdown(f"<li>{suggestion}</li>", unsafe_allow_html=True)
        st.markdown("</ul></div>", unsafe_allow_html=True)

        report = generate_processops_report(df)
        st.text_area("ProcessOps Report Preview", report, height=420)
        st.download_button(
            "Download ProcessOps Report",
            data=report,
            file_name="processops_improvement_report.txt",
            mime="text/plain",
            width="stretch",
        )

    with tabs[5]:
        st.subheader("Raw Process Log Data")
        st.dataframe(df, width="stretch")

# =============================================================================
# MAIN APP
# =============================================================================
sync_page_from_query()
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
