"""
ClinicalTrials.gov API client with pagination, rate limiting, and retry logic
API Documentation: https://clinicaltrials.gov/data-api/api
"""

import time
import logging
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class ClinicalTrialsAPIClient:
    """Client for ClinicalTrials.gov REST API v2 with rate limiting and retry logic"""

    BASE_URL = "https://clinicaltrials.gov/api/v2"

    # Rate limiting: 20 requests per second max (being conservative)
    RATE_LIMIT_DELAY = 0.05  # 50ms between requests

    # Pagination
    DEFAULT_PAGE_SIZE = 100
    MAX_PAGE_SIZE = 1000

    def __init__(
        self, max_retries: int = 3, backoff_factor: float = 0.3, timeout: int = 30
    ):
        """
        Initialize the ClinicalTrials.gov API client

        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for retries
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.last_request_time = 0

        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last_request)

        self.last_request_time = time.time()

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
    ) -> Dict[str, Any]:
        """
        Make an API request with rate limiting and error handling

        Args:
            endpoint: API endpoint path
            params: Query parameters
            method: HTTP method

        Returns:
            JSON response data
        """
        self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            logger.debug(f"Making {method} request to {url} with params: {params}")

            if method == "GET":
                response = self.session.get(url, params=params, timeout=self.timeout)
            elif method == "POST":
                response = self.session.post(url, json=params, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def search_studies(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_results: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Search for clinical trials with pagination

        Args:
            query: Search query string
            filters: Filter criteria (e.g., {"studyType": "Interventional"})
            fields: Specific fields to retrieve
            page_size: Number of results per page
            max_results: Maximum total results to retrieve

        Yields:
            Individual study records
        """
        page_size = min(page_size, self.MAX_PAGE_SIZE)

        params = {"pageSize": page_size, "format": "json"}

        if query:
            params["query.term"] = query

        if filters:
            for key, value in filters.items():
                params[f"filter.{key}"] = value

        if fields:
            params["fields"] = ",".join(fields)

        total_retrieved = 0
        next_page_token = None

        while True:
            if next_page_token:
                params["pageToken"] = next_page_token

            try:
                response = self._make_request("studies", params=params)

                studies = response.get("studies", [])

                for study in studies:
                    if max_results and total_retrieved >= max_results:
                        return

                    yield study
                    total_retrieved += 1

                logger.info(f"Retrieved {total_retrieved} studies so far")

                # Check if there are more pages
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            except Exception as e:
                logger.error(f"Error during pagination: {e}")
                break

        logger.info(f"Total studies retrieved: {total_retrieved}")

    def get_study_by_nct_id(self, nct_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific study by NCT ID

        Args:
            nct_id: NCT identifier (e.g., "NCT00000001")

        Returns:
            Study data or None if not found
        """
        try:
            response = self._make_request(f"studies/{nct_id}")
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Study {nct_id} not found")
                return None
            raise

    def get_studies_updated_since(
        self,
        date: datetime,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_results: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Get studies updated since a specific date

        Args:
            date: Datetime to check for updates
            page_size: Number of results per page
            max_results: Maximum total results to retrieve

        Yields:
            Updated study records
        """
        date_str = date.strftime("%Y-%m-%d")

        filters = {"lastUpdatePostDate": f"{date_str}"}

        return self.search_studies(
            filters=filters, page_size=page_size, max_results=max_results
        )

    def get_completed_trials(
        self,
        condition: Optional[str] = None,
        intervention: Optional[str] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        max_results: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Get completed clinical trials

        Args:
            condition: Optional condition filter
            intervention: Optional intervention filter
            page_size: Number of results per page
            max_results: Maximum total results to retrieve

        Yields:
            Completed study records
        """
        filters = {"overallStatus": "COMPLETED"}

        query_parts = []
        if condition:
            query_parts.append(condition)
        if intervention:
            query_parts.append(intervention)

        query = " AND ".join(query_parts) if query_parts else None

        return self.search_studies(
            query=query, filters=filters, page_size=page_size, max_results=max_results
        )

    def get_study_fields(self) -> List[str]:
        """
        Get list of available study fields from the API

        Returns:
            List of available field names
        """
        try:
            response = self._make_request("studies/metadata")
            return response.get("fields", [])
        except Exception as e:
            logger.error(f"Error fetching study fields: {e}")
            return []

    def get_api_version(self) -> Dict[str, Any]:
        """
        Get API version information

        Returns:
            API version details
        """
        try:
            response = self._make_request("version")
            return response
        except Exception as e:
            logger.error(f"Error fetching API version: {e}")
            return {}
