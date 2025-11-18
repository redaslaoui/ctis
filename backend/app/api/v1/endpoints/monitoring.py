from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()


@router.get("/kpis/{trial_id}")
async def get_trial_kpis(trial_id: str, db: Session = Depends(get_db)):
    """Get trial KPIs including enrollment rates"""
    return {"trial_id": trial_id, "kpis": {}}


@router.get("/alerts/{trial_id}")
async def get_trial_alerts(trial_id: str, db: Session = Depends(get_db)):
    """Get alerts for trial monitoring"""
    return {"trial_id": trial_id, "alerts": []}
