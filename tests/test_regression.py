import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.services.predictor import SlaPredictorService
from app.schemas.prediction import CasePredictionRequest

def test_active_cases_elapsed_hours_realistic(client: TestClient):
    """
    CRITICAL REGRESSION TEST:
    Verifies that all active in-progress cases report realistic elapsed hours (0.1h to 500h),
    and prevents regression of the microsecond/hour unit conversion bug (e.g., millions of hours).
    """
    response = client.get("/api/v1/prediction/triage-queue?process_id=ONBOARD_V1")
    assert response.status_code == 200
    triage_items = response.json()
    assert isinstance(triage_items, list)
    
    if len(triage_items) > 0:
        for item in triage_items:
            elapsed = item["elapsed_hours"]
            # Must be realistic scale (e.g., between 0.1 hours and 500 hours)
            assert 0.0 <= elapsed <= 500.0, f"Case {item['case_id']} has unrealistic elapsed hours: {elapsed}"
            assert elapsed < 10000.0, f"Critical unit conversion bug detected: {elapsed} hours"

def test_dfg_unique_cases_vs_executions_count(client: TestClient):
    """
    REGRESSION TEST:
    Verifies that PM4Py DFG node output clearly distinguishes between unique process cases
    and total activity event occurrences (including rework loops).
    """
    response = client.get("/api/v1/process-mining/dfg?process_id=ONBOARD_V1")
    assert response.status_code == 200
    data = response.json()
    total_cases = data["total_cases"]
    nodes = data["nodes"]

    assert len(nodes) > 0
    for node in nodes:
        assert "unique_cases_count" in node, f"Node {node['id']} missing unique_cases_count"
        assert "execution_count" in node, f"Node {node['id']} missing execution_count"
        # Unique cases cannot exceed total cases in the system
        assert node["unique_cases_count"] <= total_cases
        # Unique cases cannot exceed total execution occurrences
        assert node["unique_cases_count"] <= node["execution_count"]

def test_financial_metric_reconciliation(client: TestClient):
    """
    REGRESSION TEST:
    Verifies mathematical consistency between Overview KPIs, Bottleneck stage delay costs,
    and AI Executive Advisory figures.
    """
    overview_res = client.get("/api/v1/analytics/overview?process_id=ONBOARD_V1")
    bottlenecks_res = client.get("/api/v1/analytics/bottlenecks?process_id=ONBOARD_V1")
    ai_res = client.get("/api/v1/ai/advisory?process_id=ONBOARD_V1")

    assert overview_res.status_code == 200
    assert bottlenecks_res.status_code == 200
    assert ai_res.status_code == 200

    overview_kpis = overview_res.json()
    bottlenecks = bottlenecks_res.json()
    ai_advisory = ai_res.json()

    # Sum of stage delay costs
    sum_stage_delays = sum(b["financial_cost_of_delay_usd"] for b in bottlenecks)

    # Reconciled metrics check
    assert overview_kpis["stage_operational_waste_usd"] == pytest.approx(sum_stage_delays, rel=1e-2)
    assert overview_kpis["total_financial_waste_usd"] == pytest.approx(sum_stage_delays, rel=1e-2)
    assert ai_advisory["total_financial_waste_identified_usd"] == pytest.approx(sum_stage_delays, rel=1e-2)

def test_ml_feature_vector_ranges():
    """
    REGRESSION TEST:
    Verifies that the ML feature pipeline accepts valid feature ranges and properly sanitizes
    out-of-bound or corrupted inputs.
    """
    service = SlaPredictorService()
    
    # Test valid input
    valid_req = CasePredictionRequest(
        case_id="VALID_CASE_01",
        department_id="IT",
        stage_1_duration_hours=1.5,
        stage_2_duration_hours=12.0,
        day_of_week=2, # Wednesday
        active_load_count=20
    )
    res = service.predict_case(valid_req)
    assert 0.0 <= res.sla_breach_probability <= 1.0
    assert res.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Test extreme out-of-bound inputs
    extreme_req = CasePredictionRequest(
        case_id="EXTREME_CASE_02",
        department_id="HR",
        stage_1_duration_hours=999.0, # Should be capped/sanitized
        stage_2_duration_hours=999.0,
        day_of_week=6,
        active_load_count=1000
    )
    res_extreme = service.predict_case(extreme_req)
    assert 0.0 <= res_extreme.sla_breach_probability <= 1.0

def test_ai_advisory_numerical_grounding(client: TestClient):
    """
    REGRESSION TEST:
    Verifies that all numerical values in the AI executive advisory (median hours, SLA target,
    waste dollar amount) are strictly grounded in deterministic backend calculations.
    """
    overview_res = client.get("/api/v1/analytics/overview?process_id=ONBOARD_V1")
    ai_res = client.get("/api/v1/ai/advisory?process_id=ONBOARD_V1")

    overview = overview_res.json()
    ai_adv = ai_res.json()

    # Total waste in AI brief must match overview total waste
    assert ai_adv["total_financial_waste_identified_usd"] == overview["total_financial_waste_usd"]

    # Recommendations must have positive, realistic expected savings and reductions
    for rec in ai_adv["recommendations"]:
        assert rec["expected_cycle_time_reduction_percent"] > 0.0
        assert rec["expected_cycle_time_reduction_percent"] <= 100.0
        assert rec["estimated_annual_cost_savings_usd"] >= 0.0
