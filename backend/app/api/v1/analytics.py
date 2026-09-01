from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.analytics_engine import AnalyticsEngine
from app.schemas.analytics import OverviewKPIs, BottleneckStage, DepartmentMetric, SlaDistribution

router = APIRouter(prefix="/analytics", tags=["Operational Analytics & KPIs"])

@router.get("/overview", response_model=OverviewKPIs)
def get_overview_kpis(process_id: str = "ONBOARD_V1", db: Session = Depends(get_db)):
    """Retrieve deterministic executive KPIs (cycle times, SLA compliance, rework rate, financial waste)."""
    engine = AnalyticsEngine(db)
    return engine.get_overview_kpis(process_id=process_id)

@router.get("/bottlenecks", response_model=List[BottleneckStage])
def get_bottleneck_analysis(process_id: str = "ONBOARD_V1", db: Session = Depends(get_db)):
    """Retrieve stage-by-stage bottleneck analysis, rework rates, and Bottleneck Severity Index (BSI)."""
    engine = AnalyticsEngine(db)
    return engine.get_bottlenecks(process_id=process_id)

@router.get("/departments", response_model=List[DepartmentMetric])
def get_department_benchmarks(process_id: str = "ONBOARD_V1", db: Session = Depends(get_db)):
    """Retrieve cross-department performance benchmarks, SLA breach rates, and operational costs."""
    engine = AnalyticsEngine(db)
    return engine.get_department_metrics(process_id=process_id)

@router.get("/sla", response_model=SlaDistribution)
def get_sla_distribution(process_id: str = "ONBOARD_V1", db: Session = Depends(get_db)):
    """Retrieve SLA compliance distribution broken down by department and process variant."""
    engine = AnalyticsEngine(db)
    return engine.get_sla_distribution(process_id=process_id)
