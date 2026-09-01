from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DFGNode(BaseModel):
    id: str
    label: str
    department_id: Optional[str] = None
    unique_cases_count: int
    execution_count: int
    avg_duration_hours: float
    median_duration_hours: float
    is_start: bool = False
    is_end: bool = False
    is_bottleneck: bool = False

class DFGEdge(BaseModel):
    id: str
    source: str
    target: str
    transition_count: int
    avg_transition_hours: float
    median_transition_hours: float
    is_rework_loop: bool = False

class DFGResponse(BaseModel):
    process_id: str
    total_cases: int
    nodes: List[DFGNode]
    edges: List[DFGEdge]

class ProcessVariant(BaseModel):
    variant_id: str
    path: List[str]
    case_count: int
    percentage: float
    avg_duration_hours: float
    median_duration_hours: float
    sla_breach_rate_percent: float
    is_happy_path: bool
    description: str

class VariantsResponse(BaseModel):
    process_id: str
    total_variants_discovered: int
    variants: List[ProcessVariant]
