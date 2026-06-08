# SupportOps Intelligence Platform

A Python, SQL, NLP-style, and Streamlit-based customer support analytics platform that detects SLA breaches, resolution delays, customer sentiment trends, escalation risk, agent workload imbalance, and root-cause issues.

## Why this project exists

Customer support teams handle large volumes of tickets every day. Managers need to know which tickets are late, which customers are frustrated, which agents or departments are overloaded, and what process changes can reduce escalations.

This project converts support ticket data into operational insights and business recommendations.

## What the project does

- Generates realistic support ticket data
- Calculates support KPIs
- Detects SLA breaches
- Analyzes customer sentiment using rule-based NLP logic
- Scores escalation risk from 0 to 100
- Identifies root-cause patterns by department, issue type, and priority
- Builds an interactive Streamlit dashboard
- Produces business recommendations for process improvement

## Tech Stack

- Python
- Pandas
- Streamlit
- Plotly
- SQL
- Rule-based NLP
- Pytest

## How to Run

### 1. Create virtual environment

```bash
python -m venv .venv
```

### 2. Activate virtual environment

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

Mac/Linux:

```bash
source .venv/bin/activate
```

### 3. Install packages

```bash
pip install -r requirements.txt
```

### 4. Generate sample data

```bash
python app/data_generator.py
```

### 5. Run dashboard

```bash
streamlit run app/dashboard.py
```

## Business Questions Answered

1. What is the SLA breach rate?
2. Which departments are slowest?
3. Which issue types create the most escalations?
4. Which customers are most frustrated?
5. Which agents are overloaded?
6. Which tickets should be prioritized first?
7. What operational improvements should the business make?

## Resume Bullet

Built a customer support operations intelligence platform using Python, Pandas, SQL, and Streamlit to analyze ticket volume, SLA breaches, resolution time, customer sentiment, escalation risk, agent performance, and root-cause trends; developed a risk scoring and recommendation engine to support process improvement decisions.
