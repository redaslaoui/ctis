"""
Health check and monitoring service for the application
"""

import logging
from typing import Dict, Any
from datetime import datetime
from app.core.config import settings
from app.rag.vector_store import TrialVectorStore
from app.services.cache import cache_service
from app.core.database import SessionLocal
import requests

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Service for performing health checks on system components"""

    def __init__(self):
        """Initialize the health check service"""
        pass

    def check_database(self) -> Dict[str, Any]:
        """
        Check PostgreSQL database connection

        Returns:
            Health status dictionary
        """
        try:
            db = SessionLocal()
            # Try a simple query
            db.execute("SELECT 1")
            db.close()

            return {
                "status": "healthy",
                "message": "Database connection successful",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    def check_redis(self) -> Dict[str, Any]:
        """
        Check Redis connection

        Returns:
            Health status dictionary
        """
        try:
            if cache_service.redis_client:
                cache_service.redis_client.ping()
                stats = cache_service.get_stats()

                return {
                    "status": "healthy",
                    "message": "Redis connection successful",
                    "stats": stats,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Redis client not initialized",
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    def check_weaviate(self) -> Dict[str, Any]:
        """
        Check Weaviate vector store connection

        Returns:
            Health status dictionary
        """
        try:
            vector_store = TrialVectorStore()

            # Get statistics
            stats = vector_store.get_statistics()

            return {
                "status": "healthy",
                "message": "Weaviate connection successful",
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Weaviate health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"Weaviate connection failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    def check_clinicaltrials_api(self) -> Dict[str, Any]:
        """
        Check ClinicalTrials.gov API availability

        Returns:
            Health status dictionary
        """
        try:
            response = requests.get(
                "https://clinicaltrials.gov/api/v2/version", timeout=5
            )

            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "message": "ClinicalTrials.gov API accessible",
                    "api_version": response.json(),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            else:
                return {
                    "status": "degraded",
                    "message": f"ClinicalTrials.gov API returned status {response.status_code}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
        except Exception as e:
            logger.error(f"ClinicalTrials.gov API health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"ClinicalTrials.gov API check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    def check_openai_api(self) -> Dict[str, Any]:
        """
        Check OpenAI API availability

        Returns:
            Health status dictionary
        """
        try:
            if not settings.OPENAI_API_KEY:
                return {
                    "status": "unhealthy",
                    "message": "OpenAI API key not configured",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            # We won't make an actual API call to avoid costs
            # Just verify the key is set
            return {
                "status": "healthy",
                "message": "OpenAI API key configured",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"OpenAI API health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": f"OpenAI API check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
            }

    def comprehensive_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check on all components

        Returns:
            Overall health status dictionary
        """
        checks = {
            "database": self.check_database(),
            "redis": self.check_redis(),
            "weaviate": self.check_weaviate(),
            "clinicaltrials_api": self.check_clinicaltrials_api(),
            "openai_api": self.check_openai_api(),
        }

        # Determine overall status
        statuses = [check["status"] for check in checks.values()]

        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        return {
            "overall_status": overall_status,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global health check service instance
health_service = HealthCheckService()
