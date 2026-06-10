# OpsIntel AI

**OpsIntel AI** is an LLM-powered operations intelligence platform built with **Python, Streamlit, Pandas, Plotly, and Google Gemini API**.

The platform converts business data into actionable insights across three areas:

* **SupportOps Analyzer** — support ticket risk analysis, SLA monitoring, AI ticket triage, and manager briefings
* **CostOps Analyzer** — budget variance, vendor spend analysis, and savings opportunity reporting
* **NextHire AI** — resume-job matching, skill-gap analysis, Gemini resume coaching, and candidate reports

The system uses **Gemini API for AI analysis** and includes **rule-based fallback logic** so the app can still run safely when an API key is unavailable.

---

## Why this project exists

Business teams often have useful data, but they lose time turning that data into decisions.

Support teams need to know which tickets are risky.
Managers need daily operational briefings.
Finance teams need to understand overspending patterns.
Recruiters and candidates need faster resume-job fit analysis.

OpsIntel AI solves this by turning raw CSV-style business data into KPIs, risk signals, AI-generated recommendations, and downloadable reports.

---

## What this project demonstrates

* Google Gemini API integration
* Structured JSON output from LLM responses
* Rule-based fallback logic for safe execution
* Streamlit session state, caching, and modular page workflows
* End-to-end data pipeline: upload/demo data → validation → KPI calculation → risk scoring → AI analysis
* SaaS-style dashboard UI using custom embedded CSS
* Manager-ready reporting and downloadable outputs
* Practical AI use cases for operations, cost control, and hiring intelligence

---

## Key Features

### SupportOps Analyzer

SupportOps analyzes customer support ticket data and identifies operational risk.

Features:

* CSV upload or demo support dataset
* Required-column validation
* Data quality scoring
* SLA breach analysis
* Escalation risk scoring
* Agent workload analysis
* Issue-type and department summaries
* High-risk ticket detection
* Gemini-powered ticket triage
* Gemini-powered daily manager briefing
* Rule-based fallback if Gemini is unavailable

---

### CostOps Analyzer

CostOps analyzes budget and spend data to identify overspending patterns and savings opportunities.

Features:

* Budget vs actual spend comparison
* Department-level variance analysis
* Vendor spend concentration
* Cost category risk levels
* Estimated savings opportunity
* Downloadable cost report

---

### NextHire AI

NextHire AI compares a resume against a job description and generates candidate coaching.

Features:

* Resume-job match score
* Matched keyword analysis
* Missing skill/keyword analysis
* Gemini-powered resume coaching
* Strengths and gap analysis
* Interview preparation questions
* Gemini-powered downloadable candidate report
* Keyword-based fallback feedback

---

## AI Capabilities

OpsIntel AI uses Gemini for:

* Support ticket triage
* Customer response drafts
* Support manager daily briefings
* Resume coaching
* Candidate report generation

If `GEMINI_API_KEY` is missing or the API call fails, the app continues working using rule-based fallback logic.

---

## Tech Stack

* **Python**
* **Streamlit**
* **Pandas**
* **Plotly**
* **Google Gemini API**
* **Rule-based fallback agents**
* **Custom CSS**
* **CSV-based data workflows**

---

## Project Structure

```text
supportops-intelligence-platform/
│
├── app/
│   └── dashboard.py
│
├── ai_agent/
│   ├── agent.py
│   ├── briefing_agent.py
│   ├── action_planner.py
│   ├── response_generator.py
│   └── tools.py
│
├── data/
│   └── raw/
│       └── support_tickets.csv
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## How to Run Locally

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the virtual environment

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install packages

```bash
python -m pip install -r requirements.txt
```

### 4. Set Gemini API key

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

macOS/Linux:

```bash
export GEMINI_API_KEY="your_api_key_here"
```

Do not commit API keys to GitHub.

### 5. Run the dashboard

```bash
python -m streamlit run app/dashboard.py
```

---

## Environment Variables

```text
GEMINI_API_KEY=your_google_gemini_api_key
GEMINI_MODEL=gemini-3.1-flash-lite
```

`GEMINI_MODEL` is optional. If not provided, the app uses the default model configured in the code.

---

## Business Questions Answered

SupportOps:

1. Which tickets are highest risk?
2. Which departments have the worst SLA breach rates?
3. Which customers may need proactive communication?
4. Which agents are overloaded?
5. What actions should managers take today?

CostOps:

1. Which departments are over budget?
2. Which vendors represent the largest spend?
3. Which cost categories show high variance?
4. Where are the estimated savings opportunities?

NextHire AI:

1. How well does a resume match a job description?
2. Which skills are strong?
3. Which skills or keywords are missing?
4. What resume improvements should the candidate make?
5. What interview questions should the candidate prepare for?

---

## Security Notes

* API keys are not stored in the codebase
* `.env` and `.streamlit/secrets.toml` should be ignored by Git
* Gemini API calls include fallback handling
* The app can run without an API key using rule-based logic
* AI-generated insights should be reviewed by a human before business use

---

## Future Improvements

Planned improvements:

* Chat with support ticket data
* Multi-resume ranking against one job description
* Gemini-powered CostOps narrative analysis
* PDF report export
* Resume bullet rewriting assistant
* Streamlit Cloud deployment

---

## Resume Bullet

Built **OpsIntel AI**, a Gemini-powered operations intelligence platform using Python, Streamlit, Pandas, Plotly, and Google Gemini API to automate support ticket triage, daily manager briefings, resume-job matching, and AI-generated reports with rule-based fallback handling.

---

## Author

**Saravanakumar Subramanian**
M.S. Engineering Management, Robert Morris University
Business Analyst / Operations Analyst / AI Operations Projects

---

## Disclaimer

This is a portfolio project using demo data. AI-generated insights should be reviewed by a human before being used for real business decisions.
