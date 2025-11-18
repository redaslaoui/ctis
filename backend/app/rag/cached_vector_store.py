"""
Cached wrapper for the vector store with Redis caching
"""

from typing import List, Dict, Any, Optional
from app.rag.vector_store import TrialVectorStore
from app.services.cache import cached, cache_service
import logging

logger = logging.getLogger(__name__)


class CachedTrialVectorStore(TrialVectorStore):
    """Cached version of TrialVectorStore with Redis caching for queries"""

    def __init__(self):
        """Initialize the cached vector store"""
        super().__init__()
        self.cache = cache_service

    @cached("similar_trials", ttl=1800)  # 30 minutes
    def find_similar_trials(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar trials using vector search (cached)

        Args:
            query: Search query text
            limit: Maximum number of results
            filters: Optional Weaviate filters

        Returns:
            List of similar trials with metadata
        """
        return super().find_similar_trials(query, limit, filters)

    @cached("trials_by_condition", ttl=3600)  # 1 hour
    def find_by_condition(
        self,
        condition: str,
        phase: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find trials by medical condition (cached)

        Args:
            condition: Medical condition to search for
            phase: Optional phase filter
            limit: Maximum number of results

        Returns:
            List of matching trials
        """
        return super().find_by_condition(condition, phase, limit)

    @cached("successful_trials", ttl=7200)  # 2 hours
    def find_successful_trials(
        self,
        condition: Optional[str] = None,
        phase: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find successful trials (cached)

        Args:
            condition: Optional condition filter
            phase: Optional phase filter
            limit: Maximum number of results

        Returns:
            List of successful trials
        """
        return super().find_successful_trials(condition, phase, limit)

    @cached("trials_by_sponsor", ttl=3600)  # 1 hour
    def find_by_sponsor(
        self,
        sponsor: str,
        phase: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find trials by sponsor (cached)

        Args:
            sponsor: Sponsor name or partial name
            phase: Optional phase filter
            limit: Maximum number of results

        Returns:
            List of matching trials
        """
        return super().find_by_sponsor(sponsor, phase, limit)

    @cached("trial_by_nct", ttl=7200)  # 2 hours
    def get_trial_by_nct_id(self, nct_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific trial by NCT ID (cached)

        Args:
            nct_id: NCT identifier

        Returns:
            Trial data or None if not found
        """
        return super().get_trial_by_nct_id(nct_id)

    @cached("trial_stats", ttl=1800)  # 30 minutes
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the trials (cached)

        Returns:
            Dictionary with statistics
        """
        return super().get_statistics()

    def invalidate_cache(self, pattern: Optional[str] = None):
        """
        Invalidate cache for specific pattern or all trial caches

        Args:
            pattern: Optional cache key pattern to clear
        """
        if pattern:
            count = self.cache.clear_pattern(pattern)
            logger.info(f"Invalidated {count} cache entries matching: {pattern}")
        else:
            # Clear all trial-related caches
            patterns = [
                "similar_trials:*",
                "trials_by_condition:*",
                "successful_trials:*",
                "trials_by_sponsor:*",
                "trial_by_nct:*",
                "trial_stats:*",
                "recent_trials:*"
            ]
            total = 0
            for pat in patterns:
                total += self.cache.clear_pattern(pat)
            logger.info(f"Invalidated {total} total cache entries")

    def add_trial(self, trial_data: dict) -> str:
        """
        Add a trial to the vector store and invalidate relevant caches

        Args:
            trial_data: Dictionary containing trial information

        Returns:
            UUID of the created object
        """
        result = super().add_trial(trial_data)

        # Invalidate caches that might be affected
        self.cache.clear_pattern("similar_trials:*")
        self.cache.clear_pattern("trial_stats:*")

        # Invalidate condition-specific caches if conditions are present
        if trial_data.get("conditions"):
            for condition in trial_data["conditions"]:
                self.cache.clear_pattern(f"trials_by_condition:*{condition}*")

        # Invalidate sponsor cache if sponsor is present
        if trial_data.get("sponsor"):
            self.cache.clear_pattern(f"trials_by_sponsor:*{trial_data['sponsor']}*")

        return result
