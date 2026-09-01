from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.predictor import SlaPredictorService
from app.schemas.prediction import CasePredictionRequest, CasePredictionResponse, BatchTriageItem

router = APIRouter(prefix="/prediction", tags=["Predictive Machine Learning"])

predictor_service = SlaPredictorService()

@router.post("/sla-risk", response_model=CasePredictionResponse)
def predict_single_case_sla_risk(req: CasePredictionRequest):
    """
    Evaluates early-stage operational parameters to predict downstream SLA violation risk.
    """
    return predictor_service.predict_case(req)

@router.get("/triage-queue", response_model=List[BatchTriageItem])
def get_live_triage_queue(process_id: str = "ONBOARD_V1", db: Session = Depends(get_db)):
    """
    Real-time triage queue evaluating all active in-progress onboarding cases, 
    ranked by predicted breach probability for proactive manager intervention.
    """
    return predictor_service.get_live_triage_queue(db, process_id=process_id)
