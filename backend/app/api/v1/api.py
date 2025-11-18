from fastapi import APIRouter
from app.api.v1.endpoints import trials, predictions, monitoring, health

api_router = APIRouter()

api_router.include_router(trials.router, prefix="/trials", tags=["trials"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
