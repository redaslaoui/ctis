from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class TrialPhase(str, enum.Enum):
    PHASE_1 = "Phase 1"
    PHASE_2 = "Phase 2"
    PHASE_3 = "Phase 3"
    PHASE_4 = "Phase 4"


class TrialStatus(str, enum.Enum):
    RECRUITING = "Recruiting"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    TERMINATED = "Terminated"
    SUSPENDED = "Suspended"


class Trial(Base):
    __tablename__ = "trials"

    id = Column(Integer, primary_key=True, index=True)
    nct_id = Column(String, unique=True, index=True)
    title = Column(String)
    phase = Column(Enum(TrialPhase))
    status = Column(Enum(TrialStatus))
    sponsor = Column(String)
    condition = Column(String)
    intervention = Column(String)
    enrollment_target = Column(Integer)
    enrollment_actual = Column(Integer)
    start_date = Column(DateTime)
    completion_date = Column(DateTime)

    # Prediction results
    risk_score = Column(Float)
    risk_factors = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
