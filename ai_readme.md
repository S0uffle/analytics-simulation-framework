# AI README: Analytics Simulation Framework

## 1. Project Overview
This repository contains an **Analytics Business Framework** implemented as a Python Streamlit Web Dashboard. Its core purpose is to model, visualize, and optimize a **5-Step Data Flywheel** for mobile applications (Mobile Apps/Games). It acts as an "All-in-one" decision support system based on data.

## 2. Tech Stack
- **Frontend/Dashboard:** Streamlit (`streamlit`), Plotly (`plotly`)
- **Data Processing:** Pandas, NumPy
- **Machine Learning & Simulation:** Scikit-learn, SciPy (for Monte Carlo simulations)
- **Data Source/Storage:** Google Cloud BigQuery (optional, falls back to sample data), `pydantic` and `python-dotenv` for config

## 3. Directory Structure
- `app.py`: Main entry point for the Streamlit dashboard.
- `config.py`: Python configuration file defining dataclass structures, baseline logic, UA costs, and Ads settings. Auto-loads overrides from `sim_config.json`.
- `sim_config.json`: **[NEW]** The single-source-of-truth configuration file containing all active parameters (UA, Ads, Subscriptions, Retention, Variations, Checkboxes). Both the UI and headless scripts read from here.
- `run_headless_simulation.py`: **[NEW]** Script used by the AI Agent to run the Monte Carlo simulation silently in the background and analyze results without opening the Streamlit UI.
- `requirements.txt`: Python dependencies.
- `modules/`: Contains the core logic for the 5-step flywheel:
  - `simulation.py`: Monte Carlo simulation & KPI generation (**Focus Area**).
  - `prediction.py`: ML models (pLTV, Churn Prediction).
  - `monitoring.py`: Health score calculation, alerts, and pacing tracker.
  - `analysis.py`: Cohort, Funnel, and Drill-down analysis.
  - `action.py`: Automated rules and personalized recommendations.
- `components/`: UI components and charts (Plotly).
- `data/`: Sample data generation and loaders.
- `sql/` & `BIGQUERY_SETUP.md`: BigQuery queries and setup instructions.

## 4. Focus Area: Simulation Module (`modules/simulation.py`)
The user has indicated that **upcoming sessions will focus on reviewing and optimizing the simulation mechanism**. 

**Core Components:**
- **`EnhancedMonteCarloSimulator`**: Uses Monte Carlo methods to run "What-if" scenarios over an N-day lifecycle (e.g., 365 days). It has two modes:
  - *Stochastic (Random)*: Samples input parameters (CPI, CTR, CVR, eCPM, retention multipliers) from a normal distribution based on standard deviations specified in config.
  - *Deterministic*: Uses exact mean values when variations are set to 0.
- **Metrics Calculated**: 
  - User Acquisition (UA): Blended CPI vs Paid CPI.
  - In-App Advertising (IAA): Daily revenue calculated as `Retention * ARPDAU`. Includes mathematical decay mechanisms for eCPM and Impressions over the user lifecycle.
  - In-App Purchases (IAP) / Subscriptions: Models trial-to-paid conversions, auto-renewals, retention across subscription cycles, and platform fees (e.g., Apple/Google 15-30% cut).
- **`TargetKPIGenerator`**: Processes the results of `N` simulation runs (e.g., 500) and extracts percentiles (P5, P25, P50, P75, P95) to set target ranges (Pessimistic, Safe, Expected, Breakthrough, Optimistic).

**Optimization Opportunities (For AI Agents):**
- Improve the statistical robustness or performance of the Monte Carlo loop (e.g., utilizing NumPy vectorization instead of Python `for` loops).
- Refine the decay functions for eCPM/Impressions to better reflect real-world Ad-network behaviors.
- Improve subscription renewal modeling logic or retention curves.
- Reduce simulation execution time so the Streamlit UI feels more responsive.

## 5. Agent Workflow & Instructions
1. **Running the App**: 
   - A `.venv` virtual environment is configured.
   - Command to test: `source .venv/bin/activate && streamlit run app.py`.
2. **Modifying Config & Testing**: 
   - Modifying parameters: Update `sim_config.json` to change simulation parameters (prices, retention, plan toggles, variations). `config.py` automatically parses this file.
   - Running Headless Simulation: Use `source .venv/bin/activate && python run_headless_simulation.py` to quickly test the outcome of the simulation based on `sim_config.json` parameters.
3. **Language & Tone**: The user communicates in Vietnamese. The AI must respond in Vietnamese with a professional, concise, and focused tone (No Hallucinations). Code, variables, and technical concepts should remain in English.
4. **Self-Healing & Validation**: If you encounter errors while testing code, try to self-correct up to 3 times before asking the user. Always validate facts using tools (e.g., checking file contents) rather than assuming.

## 6. Git Workflow & Remote Setup
Để quản lý mã nguồn và tiếp tục làm việc trên dự án ở các máy tính khác nhau, hãy tuân thủ quy trình Git.