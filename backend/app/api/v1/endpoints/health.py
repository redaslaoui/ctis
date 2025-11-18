"""
Health check and monitoring endpoints
"""

from fastapi import APIRouter, status
from typing import Dict, Any
from app.services.health import health_service
from app.services.cache import cache_service
from app.rag.cached_vector_store import CachedTrialVectorStore

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Simple health check endpoint

    Returns:
        Basic health status
    """
    return {
        "status": "healthy",
        "service": "Clinical Trial Intelligence Platform",
        "version": "0.1.0"
    }


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for all components

    Returns:
        Detailed health status for all services
    """
    return health_service.comprehensive_health_check()


@router.get("/health/database", status_code=status.HTTP_200_OK)
async def database_health() -> Dict[str, Any]:
    """
    Database health check

    Returns:
        Database connection status
    """
    return health_service.check_database()


@router.get("/health/redis", status_code=status.HTTP_200_OK)
async def redis_health() -> Dict[str, Any]:
    """
    Redis health check

    Returns:
        Redis connection status and stats
    """
    return health_service.check_redis()


@router.get("/health/weaviate", status_code=status.HTTP_200_OK)
async def weaviate_health() -> Dict[str, Any]:
    """
    Weaviate vector store health check

    Returns:
        Weaviate connection status and stats
    """
    return health_service.check_weaviate()


@router.get("/health/cache/stats", status_code=status.HTTP_200_OK)
async def cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics

    Returns:
        Cache performance metrics
    """
    return cache_service.get_stats()


@router.post("/health/cache/clear", status_code=status.HTTP_200_OK)
async def clear_cache(pattern: str = "*") -> Dict[str, Any]:
    """
    Clear cache entries matching pattern

    Args:
        pattern: Cache key pattern to clear (default: all)

    Returns:
        Number of entries cleared
    """
    vector_store = CachedTrialVectorStore()
    vector_store.invalidate_cache(pattern if pattern != "*" else None)

    return {
        "status": "success",
        "message": f"Cache cleared for pattern: {pattern}"
    }


@router.get("/monitoring/metrics", status_code=status.HTTP_200_OK)
async def get_metrics() -> Dict[str, Any]:
    """
    Get system metrics

    Returns:
        System performance metrics
    """
    try:
        vector_store = CachedTrialVectorStore()
        stats = vector_store.get_statistics()

        cache_stats_data = cache_service.get_stats()

        return {
            "vector_store": stats,
            "cache": cache_stats_data,
            "timestamp": stats.get("last_updated")
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }
