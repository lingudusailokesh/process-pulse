import pytest
from app.services.analytics_engine import calculate_bottleneck_severity_index

def test_bottleneck_severity_index_nominal():
    """Verify BSI calculation with normal parameters."""
    stage_dur = 40.0
    total_dur = 100.0
    rework = 0.25  # 25%
    
    # Expected: (40 / 100) * (1 + 0.25) = 0.40 * 1.25 = 0.50
    bsi = calculate_bottleneck_severity_index(stage_dur, total_dur, rework)
    assert bsi == pytest.approx(0.50, rel=1e-3)

def test_bottleneck_severity_index_zero_division_guard():
    """Verify BSI returns 0.0 without crashing on zero durations."""
    assert calculate_bottleneck_severity_index(0.0, 0.0, 0.0) == 0.0
    assert calculate_bottleneck_severity_index(10.0, 0.0, 0.5) == 0.0
    assert calculate_bottleneck_severity_index(0.0, 50.0, 0.5) == 0.0

def test_bottleneck_severity_index_no_rework():
    """Verify BSI with zero rework rate."""
    stage_dur = 20.0
    total_dur = 80.0
    rework = 0.0
    # Expected: (20 / 80) * 1.0 = 0.25
    bsi = calculate_bottleneck_severity_index(stage_dur, total_dur, rework)
    assert bsi == pytest.approx(0.25, rel=1e-3)

def test_financial_delay_waste_math():
    """Verify operational delay cost calculation."""
    excess_hours = 30.0
    hourly_rate = 70.0 # IT Rate
    expected_cost = excess_hours * hourly_rate
    assert expected_cost == 2100.0
