# ProcessPulse — Enterprise Process Mining & Operations Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1.svg)](https://www.mysql.com/)
[![PM4Py](https://img.shields.io/badge/Process_Mining-PM4Py-orange.svg)](https://pm4py.fit.fraunhofer.de/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

> **ProcessPulse** is an enterprise-grade operational intelligence and process mining platform engineered to answer the core executive consulting question:
> 
> *"Where is the organization losing time and money, why is it happening, and what actionable interventions will yield the highest ROI?"*

Demonstrated through the cross-functional **Enterprise Employee Onboarding & Access Provisioning** lifecycle, the platform ingests raw system event streams, algorithmically discovers workflow graphs, deterministically quantifies bottlenecks, predicts SLA violations using machine learning, and synthesizes grounded executive transformation briefs with zero hallucination.

---

## 🏛️ System Architecture

```
                                  SYSTEM ARCHITECTURE
  
  [ Client Tier ]
  ┌────────────────────────────────────────────────────────────────────────┐
  │                    Browser (Vanilla JS / React Dashboard)             │
  │  - Executive KPI Cards   - Cytoscape.js Process Flow (DFG)             │
  │  - Bottleneck Heatmaps   - Live SLA Predictor   - AI Executive Brief   │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │ HTTP REST (JSON + JWT)
                                      ▼
  [ API Gateway & Application Tier (FastAPI) ]
  ┌────────────────────────────────────────────────────────────────────────┐
  │                           FastAPI Router Layer                         │
  │  /api/v1/auth  |  /api/v1/processes  |  /api/v1/analytics  |  /api/v1/ai│
  ├───────────────────────────────────┬────────────────────────────────────┤
  │   Authentication & RBAC Filter   │ PII Anonymization & Scrubbing       │
  ├───────────────────────────────────┴────────────────────────────────────┤
  │                            Service Layer                               │
  │  ┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────┐ │
  │  │   Analytics Engine    │ │Process Mining Svc │ │Prediction Service │ │
  │  │ (Pandas / SQL Engine) │ │  (PM4Py Wrapper)  │ │   (Scikit-Learn)  │ │
  │  └───────────┬───────────┘ └─────────┬─────────┘ └─────────┬─────────┘ │
  └──────────────┼───────────────────────┼─────────────────────┼───────────┘
                 │                       │                     │
                 ▼                       ▼                     ▼
  [ Data & Computation Layer ]
  ┌────────────────────────────────────────────────────────────────────────┐
  │  ┌─────────────────────────┐               ┌─────────────────────────┐ │
  │  │   MySQL 8.0 Database    │               │  LLM Advisory Service   │ │
  │  │  - process_definitions  │               │   (Gemini Structured)   │ │
  │  │  - process_instances    │               │                         │ │
  │  │  - process_event_logs   │               │ Receives ONLY validated │ │
  │  │  - users & audit_logs   │               │ deterministic findings. │ │
  │  └─────────────────────────┘               └─────────────────────────┘ │
  └────────────────────────────────────────────────────────────────────────┘
```

---

## 💼 Deloitte Competency & Value Alignment

| Deloitte JD Requirement | Platform Implementation & Engineering Rigor |
| :--- | :--- |
| **Data Analysis & Pattern Recognition** | Ingests 500+ workflow event logs into **Pandas & PM4Py**, calculating median cycle times, interquartile ranges, and state transition matrices. |
| **Process Improvement Initiatives** | Formulates the **Bottleneck Severity Index ($BSI$)**, isolating a 46-hour IT security rejection loop responsible for 88% of SLA breaches. |
| **Application Development & REST APIs** | Modular **FastAPI** backend with versioned routing, Pydantic data schemas, dependency injection, and connection pooling. |
| **Database Architecture** | Production **MySQL 8.0** schema with composite indexing on `(case_id, event_timestamp)` for high-throughput time-series querying. |
| **Predictive Machine Learning** | Trains a **Scikit-Learn Random Forest Classifier** to triage active in-progress cases and predict SLA breach risk with explainable feature weights. |
| **Grounded Generative AI** | Google **Gemini API** integration with strict JSON schema constraints; narratives are strictly grounded on deterministic metrics with zero hallucination. |
| **Data Privacy, Security & RBAC** | Cryptographic PII pseudonymization (`SHA-256(EMP_ID + Salt)`), stateless JWT authentication, and bcrypt password encryption. |
| **Testing & Quality Standards** | Automated test suite in **Pytest** with 100% pass rate covering analytics math, REST API contracts, and security utilities. |

---

## 📐 Mathematical Rigor & Deterministic Formulas

All numerical metrics are computed deterministically in Python/SQL before being visualized or synthesized by the LLM:

1. **Median Cycle Time ($P_{50}$):** Protects operational benchmarks from skew caused by weekend submission outliers.
2. **Bottleneck Severity Index ($BSI$):**
   $$BSI_k = \left( \frac{\text{Median Duration}_k}{\text{Median Total Process Duration}} \right) \times (1 + \text{Rework Rate}_k)$$
3. **Financial Cost of Inefficiency ($FCI$):**
   $$\text{Cost of Delay}_k = \sum_{i=1}^N \max(0, \text{Duration}_{i, k} - \text{Target Duration}_k) \times \text{CostPerHour}_{\text{dept}(k)}$$
4. **Directly-Follows Graph (DFG):** Discovers all activity pairs $(a_i, a_j)$ executed contiguously in historical cases.

---

## 🛠️ Technology Stack

| Layer | Technology | Key Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI (Python 3.11+) | High-throughput REST API with OpenAPI documentation |
| **Database** | MySQL 8.0 / SQLite Fallback | Normalized relational event logs with composite indexing |
| **Analytics Engine** | Pandas & NumPy | Vectorized cycle-time and delay calculations |
| **Process Mining** | PM4Py 2.7 | Directly-Follows Graph (DFG) discovery & variant analysis |
| **Machine Learning** | Scikit-Learn (Random Forest) | Early-warning SLA breach prediction model |
| **Frontend UI** | Vanilla JS (ES6+) + Tailwind CSS | Fast, modular dashboard with zero framework bloat |
| **Visualizations** | Chart.js & Cytoscape.js | Interactive process network maps & KPI charts |
| **Generative AI** | Google Gemini API (or Heuristic) | Grounded C-suite operational transformation briefs |
| **Security & Auth** | PyJWT + Bcrypt | Stateless token auth & PII anonymization |
| **Testing** | Pytest + FastAPI TestClient | Automated validation of math and REST endpoints |
| **DevOps** | Docker & Docker Compose | Containerized multi-service deployment |

---

## 🚀 Quickstart Guide

### Option 1: Local Development (Instant Run)

1. **Clone and navigate to repository:**
   ```bash
   cd process_pulse
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Seed Database with 500+ Onboarding Cases:**
   ```bash
   python data/seed_events.py
   ```

4. **Train the SLA Breach Machine Learning Model:**
   ```bash
   python ml_models/train_sla_model.py
   ```

5. **Start the FastAPI Backend:**
   ```bash
   uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

6. **Launch the Dashboard:**
   * Open your browser and navigate to: **`http://127.0.0.1:8000/dashboard/`**
   * Interactive API Documentation (Swagger UI): **`http://127.0.0.1:8000/docs`**

---

### Option 2: Docker Compose (Production Multi-Container)

```bash
docker-compose up --build
```
* **Dashboard:** `http://localhost:8000/dashboard/`
* **MySQL Port:** `3306` (Database: `process_pulse_db`)

---

## 🧪 Automated Testing

Execute the complete 21-test suite verifying math formulas, API endpoints, security utilities, and regression guards:

```bash
pytest -v tests/
```

**Test Coverage Summary (21 Passed / 100%):**
* `test_analytics.py`: Validates BSI formula, zero-division guards, and financial delay waste calculations.
* `test_api_routes.py`: Verifies endpoints (`/overview`, `/bottlenecks`, `/dfg`, `/triage-queue`, `/ai/advisory`).
* `test_regression.py`: Guards against active case elapsed time bugs, verifies DFG unique cases vs total event occurrences, ensures financial metric reconciliation, validates ML feature vector bounds, and validates grounded AI numerical integrity.
* `test_security.py`: Verifies direct bcrypt password hashing, JWT claims decoding, and PII pseudonymization.

---

## 📊 Core REST API Catalog

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Authenticate user and issue signed JWT access token |
| `GET` | `/api/v1/analytics/overview` | Executive KPIs (Median cycle time, SLA rate, financial waste) |
| `GET` | `/api/v1/analytics/bottlenecks` | Stage-by-stage Bottleneck Severity Index ($BSI$) rankings |
| `GET` | `/api/v1/analytics/departments` | Cross-department performance benchmarks & handling costs |
| `GET` | `/api/v1/process-mining/dfg` | PM4Py Directly-Follows Graph nodes, transitions, and loops |
| `GET` | `/api/v1/process-mining/variants` | Discovered process variants (Happy Path vs Deviations) |
| `POST` | `/api/v1/prediction/sla-risk` | Real-time SLA breach probability prediction for single case |
| `GET` | `/api/v1/prediction/triage-queue`| Live queue of active cases ranked by predicted breach risk |
| `GET` | `/api/v1/ai/advisory` | Grounded executive transformation advisory brief |

---

## 🎯 Deloitte Interview Preparation & Talking Points

### 1. 30-Second Elevator Pitch
> *"I built **ProcessPulse**, an enterprise operational intelligence platform designed to answer: 'Where is a company losing time and money in its internal operations?' Using FastAPI, MySQL, and PM4Py, it transforms raw workflow event logs into interactive process maps, deterministically quantifies bottlenecks, and uses Scikit-Learn and grounded AI to predict SLA violations and recommend cost-saving process improvements."*

### 2. Why Separate Analytics from the LLM?
> *"In enterprise consulting, data integrity is paramount. LLMs are non-deterministic and prone to calculation hallucinations when analyzing raw tabular data. I architected ProcessPulse so that Python, Pandas, and PM4Py perform all mathematical calculations deterministically. The structured findings are then passed to the LLM via a strictly enforced JSON schema solely for executive synthesis and narrative generation. This guarantees 100% numerical accuracy."*

### 3. How Does the Platform Distinguish Bottlenecks from Complex Steps?
> *"We evaluate two distinct metrics: Median Waiting Time and the Rework Loop Rate. A normal step might take 24 hours due to complexity, but a structural bottleneck exhibits high queue latency combined with frequent rejection loops. Our Bottleneck Severity Index ($BSI$) weights the median stage duration by the rework percentage, allowing us to distinguish between complex value-add activities and broken handoff procedures."*

---

## 👤 Author
* **Role Focus:** Technology Consulting / Data & Process Analytics (Deloitte Analyst Candidate)
* **Stack:** Python, FastAPI, MySQL, Pandas, PM4Py, Scikit-Learn, JavaScript (ES6+), Cytoscape.js, Docker
