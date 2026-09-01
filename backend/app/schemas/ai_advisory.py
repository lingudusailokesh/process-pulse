from typing import List, Optional
from pydantic import BaseModel, Field

class StrategicRecommendation(BaseModel):
    category: str # "PROCESS", "PEOPLE", "TECHNOLOGY"
    title: str
    description: str
    target_stage: str
    expected_cycle_time_reduction_percent: float
    estimated_annual_cost_savings_usd: float
    implementation_priority: str # "IMMEDIATE (P1)", "MEDIUM (P2)", "STRATEGIC (P3)"

class RootCauseFinding(BaseModel):
    stage_name: str
    department: str
    issue_type: str # "REWORK_LOOP", "HANDOFF_LATENCY", "APPROVAL_BOTTLENECK"
    observed_metric: str
    business_impact: str

class AIExecutiveAdvisory(BaseModel):
    executive_summary: str
    overall_health_score: str # e.g. "C+ (Operational Drag Detected)"
    total_financial_waste_identified_usd: float
    root_causes: List[RootCauseFinding]
    recommendations: List[StrategicRecommendation]
    consulting_narrative: str
