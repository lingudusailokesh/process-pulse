from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.analytics_engine import AnalyticsEngine
from app.services.process_miner import ProcessMinerService
from app.services.llm_advisor import LLMAdvisorService
from app.schemas.ai_advisory import AIExecutiveAdvisory

router = APIRouter(prefix="/ai", tags=["Executive AI Advisory & Narrative Synthesis"])

llm_service = LLMAdvisorService()

@router.get("/advisory", response_model=AIExecutiveAdvisory)
def get_executive_advisory(process_id: str = "ONBOARD_V1", db: Session = Depends(get_db)):
    """
    Generates a grounded executive consulting briefing and prioritized action plan.
    All narratives are strictly grounded on deterministic analytics and process mining findings.
    """
    analytics = AnalyticsEngine(db)
    miner = ProcessMinerService(db)

    kpis = analytics.get_overview_kpis(process_id=process_id)
    bottlenecks = analytics.get_bottlenecks(process_id=process_id)
    variants_res = miner.get_process_variants(process_id=process_id)

    variants_summary = {
        "total_variants": variants_res.total_variants_discovered,
        "variants": [
            {
                "variant_id": v.variant_id,
                "case_count": v.case_count,
                "percentage": v.percentage,
                "avg_duration": v.avg_duration_hours,
                "is_happy_path": v.is_happy_path
            } for v in variants_res.variants[:3]
        ]
    }

    return llm_service.generate_advisory(
        kpis=kpis,
        bottlenecks=bottlenecks,
        variants_summary=variants_summary
    )
