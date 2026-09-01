from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class CasePredictionRequest(BaseModel):
    case_id: str
    department_id: str
    stage_1_duration_hours: float = Field(..., ge=0.0, description="Duration of employee request submission")
    stage_2_duration_hours: float = Field(..., ge=0.0, description="Duration of manager approval")
    day_of_week: int = Field(0, ge=0, le=6, description="0=Monday, 6=Sunday")
    active_load_count: int = Field(25, ge=0, description="Concurrent active cases in system")

class CasePredictionResponse(BaseModel):
    case_id: str
    department_id: str
    sla_breach_probability: float # e.g. 0.87
    risk_level: str # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    predicted_breach: bool
    top_risk_factors: List[str]
    suggested_action: str

class BatchTriageItem(BaseModel):
    case_id: str
    department_id: str
    current_stage: str
    elapsed_hours: float
    breach_probability: float
    risk_level: str
    suggested_action: str
