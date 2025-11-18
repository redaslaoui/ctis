from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class TrialBase(BaseModel):
    nct_id: str
    title: str
    phase: str
    status: str
    sponsor: str
    condition: str
    intervention: str
    enrollment_target: Optional[int] = None


class TrialCreate(TrialBase):
    pass


class TrialUpdate(BaseModel):
    enrollment_actual: Optional[int] = None
    status: Optional[str] = None


class TrialResponse(TrialBase):
    id: int
    risk_score: Optional[float] = None
    risk_factors: Optional[Dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RiskPrediction(BaseModel):
    trial_id: int
    risk_score: float
    confidence: float
    risk_factors: List[str]
    recommendations: List[str]
