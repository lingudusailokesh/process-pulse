from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.process_miner import ProcessMinerService
from app.schemas.process_mining import DFGResponse, VariantsResponse

router = APIRouter(prefix="/process-mining", tags=["Process Mining & Graph Discovery"])

@router.get("/dfg", response_model=DFGResponse)
def get_directly_follows_graph(process_id: str = "ONBOARD_V1", db: Session = Depends(get_db)):
    """
    Extracts the PM4Py Directly-Follows Graph (DFG) containing activity nodes, 
    execution statistics, transition frequencies, and rework loops.
    """
    miner = ProcessMinerService(db)
    return miner.get_directly_follows_graph(process_id=process_id)

@router.get("/variants", response_model=VariantsResponse)
def get_process_variants(process_id: str = "ONBOARD_V1", db: Session = Depends(get_db)):
    """
    Discovers all unique process execution path variants (Happy Path vs Deviations/Rework).
    """
    miner = ProcessMinerService(db)
    return miner.get_process_variants(process_id=process_id)
