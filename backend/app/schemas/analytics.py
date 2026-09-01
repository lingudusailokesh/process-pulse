from typing import List, Optional, Dict
from pydantic import BaseModel

class OverviewKPIs(BaseModel):
    total_cases: int
    completed_cases: int
    active_cases: int
    avg_cycle_time_hours: float
    median_cycle_time_hours: float
    p90_cycle_time_hours: float
    sla_compliance_rate_percent: float
    sla_breach_rate_percent: float
    rework_case_rate_percent: float
    total_financial_waste_usd: float # Consolidated total operational delay waste
    case_sla_breach_waste_usd: float # Direct SLA breach penalty (>120h)
    stage_operational_waste_usd: float # Sum of excess stage delay costs
    sla_target_hours: float

class BottleneckStage(BaseModel):
    stage_name: str
    department_id: str
    department_name: str
    median_duration_hours: float
    avg_duration_hours: float
    p90_duration_hours: float
    rework_count: int
    rework_rate_percent: float
    bottleneck_severity_index: float # BSI
    total_excess_hours: float
    financial_cost_of_delay_usd: float
    is_critical_bottleneck: bool

class DepartmentMetric(BaseModel):
    department_id: str
    department_name: str
    total_cases_handled: int
    median_handling_hours: float
    avg_handling_hours: float
    sla_breach_rate_percent: float
    hourly_rate_usd: float
    total_operational_cost_usd: float

class SlaDistribution(BaseModel):
    within_sla_count: int
    breached_sla_count: int
    compliance_rate_percent: float
    breach_rate_percent: float
    breaches_by_department: Dict[str, int]
    breaches_by_variant: Dict[str, int]

class CaseSummary(BaseModel):
    case_id: str
    department_id: str
    start_time: str
    end_time: Optional[str] = None
    status: str
    total_duration_hours: Optional[float] = None
    is_sla_breached: bool
    variant_id: Optional[str] = None
