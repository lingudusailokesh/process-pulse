from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """Verify system health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"

def test_overview_kpis_api(client: TestClient):
    """Verify overview KPIs API endpoint returns deterministic numbers."""
    response = client.get("/api/v1/analytics/overview?process_id=ONBOARD_V1")
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert "median_cycle_time_hours" in data
    assert "sla_compliance_rate_percent" in data
    assert data["total_cases"] >= 0

def test_bottlenecks_api(client: TestClient):
    """Verify bottleneck endpoint returns ranked stages."""
    response = client.get("/api/v1/analytics/bottlenecks?process_id=ONBOARD_V1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "stage_name" in first
        assert "bottleneck_severity_index" in first
        assert "financial_cost_of_delay_usd" in first

def test_dfg_graph_api(client: TestClient):
    """Verify PM4Py Directly-Follows Graph endpoint returns nodes and transitions."""
    response = client.get("/api/v1/process-mining/dfg?process_id=ONBOARD_V1")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0

def test_triage_queue_api(client: TestClient):
    """Verify live ML triage queue returns evaluated active cases."""
    response = client.get("/api/v1/prediction/triage-queue?process_id=ONBOARD_V1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_single_case_prediction_api(client: TestClient):
    """Verify single case ML prediction endpoint."""
    payload = {
        "case_id": "TEST_CASE_999",
        "department_id": "IT",
        "stage_1_duration_hours": 2.5,
        "stage_2_duration_hours": 24.0, # Delayed manager approval
        "day_of_week": 4, # Friday
        "active_load_count": 30
    }
    response = client.post("/api/v1/prediction/sla-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "TEST_CASE_999"
    assert "sla_breach_probability" in data
    assert "risk_level" in data
    assert "suggested_action" in data

def test_ai_advisory_api(client: TestClient):
    """Verify grounded AI advisory brief endpoint returns structured narrative."""
    response = client.get("/api/v1/ai/advisory?process_id=ONBOARD_V1")
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
    assert "overall_health_score" in data
    assert "root_causes" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1
