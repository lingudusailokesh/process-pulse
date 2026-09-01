from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.process import ProcessDefinition, ProcessInstance, ProcessEventLog
from app.schemas.analytics import CaseSummary

router = APIRouter(prefix="/processes", tags=["Process Definitions & Instances"])

@router.get("/definitions")
def get_process_definitions(db: Session = Depends(get_db)):
    """Retrieve all available registered enterprise process definitions."""
    procs = db.query(ProcessDefinition).all()
    return [{
        "process_id": p.process_id,
        "process_name": p.process_name,
        "description": p.description,
        "sla_hours_target": p.sla_hours_target,
        "target_cost": p.target_cost
    } for p in procs]

@router.get("/cases", response_model=List[CaseSummary])
def get_cases(
    process_id: str = "ONBOARD_V1",
    department_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List workflow cases with optional department, status, and pagination filters."""
    query = db.query(ProcessInstance).filter(ProcessInstance.process_id == process_id)
    if department_id:
        query = query.filter(ProcessInstance.department_id == department_id)
    if status:
        query = query.filter(ProcessInstance.current_status == status)

    cases = query.order_by(ProcessInstance.start_time.desc()).offset(offset).limit(limit).all()

    return [CaseSummary(
        case_id=c.case_id,
        department_id=c.department_id,
        start_time=c.start_time.isoformat(),
        end_time=c.end_time.isoformat() if c.end_time else None,
        status=c.current_status,
        total_duration_hours=c.total_duration_hours,
        is_sla_breached=c.is_sla_breached,
        variant_id=c.variant_id
    ) for c in cases]

@router.get("/cases/{case_id}/events")
def get_case_events(case_id: str, db: Session = Depends(get_db)):
    """Retrieve the chronological audit event stream for a specific case."""
    instance = db.query(ProcessInstance).filter(ProcessInstance.case_id == case_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    events = db.query(ProcessEventLog).filter(
        ProcessEventLog.case_id == case_id
    ).order_by(ProcessEventLog.event_timestamp.asc()).all()

    return {
        "case_id": instance.case_id,
        "process_id": instance.process_id,
        "department_id": instance.department_id,
        "status": instance.current_status,
        "total_duration_hours": instance.total_duration_hours,
        "is_sla_breached": instance.is_sla_breached,
        "events": [{
            "event_id": e.event_id,
            "activity_name": e.activity_name,
            "stage_order": e.stage_order,
            "actor_id": e.actor_id,
            "department_id": e.department_id,
            "timestamp": e.event_timestamp.isoformat(),
            "activity_status": e.activity_status,
            "cost_incurred": e.cost_incurred
        } for e in events]
    }
