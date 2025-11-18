import weaviate
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class TrialVectorStore:
    """Enhanced Weaviate vector store for clinical trial data with comprehensive schema"""

    def __init__(self):
        self.client = weaviate.Client(url=settings.WEAVIATE_URL)
        self._init_schema()

    def _init_schema(self):
        """Initialize comprehensive Weaviate schema for clinical trials"""
        schema = {
            "class": "ClinicalTrial",
            "description": "A comprehensive clinical trial record with vectorized search capabilities",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "model": "text-embedding-3-small",
                    "type": "text",
                    "vectorizeClassName": False,
                }
            },
            "properties": [
                # Basic Identification
                {
                    "name": "nctId",
                    "dataType": ["text"],
                    "description": "ClinicalTrials.gov NCT ID",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Official trial title",
                    "moduleConfig": {"text2vec-openai": {"skip": False}},
                },
                {
                    "name": "briefSummary",
                    "dataType": ["text"],
                    "description": "Brief summary of the trial",
                    "moduleConfig": {"text2vec-openai": {"skip": False}},
                },
                {
                    "name": "detailedDescription",
                    "dataType": ["text"],
                    "description": "Detailed description of the trial",
                    "moduleConfig": {"text2vec-openai": {"skip": False}},
                },
                # Trial Classification
                {
                    "name": "phase",
                    "dataType": ["text"],
                    "description": "Trial phase (Phase 1, 2, 3, 4)",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "status",
                    "dataType": ["text"],
                    "description": "Trial status (Recruiting, Active, Completed, Terminated)",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "studyType",
                    "dataType": ["text"],
                    "description": "Type of study (Interventional, Observational)",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                # Condition and Intervention
                {
                    "name": "conditions",
                    "dataType": ["text[]"],
                    "description": "Medical conditions being studied",
                    "moduleConfig": {"text2vec-openai": {"skip": False}},
                },
                {
                    "name": "interventions",
                    "dataType": ["text[]"],
                    "description": "Interventions or treatments being tested",
                    "moduleConfig": {"text2vec-openai": {"skip": False}},
                },
                {
                    "name": "interventionType",
                    "dataType": ["text"],
                    "description": "Type of intervention (Drug, Device, Procedure)",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                # Sponsor and Organization
                {
                    "name": "sponsor",
                    "dataType": ["text"],
                    "description": "Lead sponsor organization",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "sponsorType",
                    "dataType": ["text"],
                    "description": "Type of sponsor (Industry, Academic, Government)",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "collaborators",
                    "dataType": ["text[]"],
                    "description": "Collaborating organizations",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                # Dates and Timeline
                {
                    "name": "startDate",
                    "dataType": ["date"],
                    "description": "Trial start date",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "completionDate",
                    "dataType": ["date"],
                    "description": "Trial completion date",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "primaryCompletionDate",
                    "dataType": ["date"],
                    "description": "Primary completion date",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "lastUpdateDate",
                    "dataType": ["date"],
                    "description": "Last update posted date",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                # Enrollment
                {
                    "name": "enrollmentCount",
                    "dataType": ["int"],
                    "description": "Actual or anticipated enrollment count",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "enrollmentType",
                    "dataType": ["text"],
                    "description": "Enrollment type (Actual or Anticipated)",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                # Eligibility
                {
                    "name": "eligibilityCriteria",
                    "dataType": ["text"],
                    "description": "Eligibility criteria for participants",
                    "moduleConfig": {"text2vec-openai": {"skip": False}},
                },
                {
                    "name": "sex",
                    "dataType": ["text"],
                    "description": "Eligible sex (All, Male, Female)",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "minimumAge",
                    "dataType": ["text"],
                    "description": "Minimum age for eligibility",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "maximumAge",
                    "dataType": ["text"],
                    "description": "Maximum age for eligibility",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                # Outcomes
                {
                    "name": "primaryOutcomes",
                    "dataType": ["text[]"],
                    "description": "Primary outcome measures",
                    "moduleConfig": {"text2vec-openai": {"skip": False}},
                },
                {
                    "name": "secondaryOutcomes",
                    "dataType": ["text[]"],
                    "description": "Secondary outcome measures",
                    "moduleConfig": {"text2vec-openai": {"skip": False}},
                },
                {
                    "name": "outcomeClassification",
                    "dataType": ["text"],
                    "description": "Classified outcome (Success, Failure, Terminated, Unknown)",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "hasResults",
                    "dataType": ["boolean"],
                    "description": "Whether results have been posted",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                # Location
                {
                    "name": "locationCountries",
                    "dataType": ["text[]"],
                    "description": "Countries where trial is conducted",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "locationFacilities",
                    "dataType": ["text[]"],
                    "description": "Facility names where trial is conducted",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                # Study Design
                {
                    "name": "studyDesign",
                    "dataType": ["text"],
                    "description": "Study design information",
                    "moduleConfig": {"text2vec-openai": {"skip": False}},
                },
                {
                    "name": "armCount",
                    "dataType": ["int"],
                    "description": "Number of study arms",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                # Composite text for rich embeddings
                {
                    "name": "compositeText",
                    "dataType": ["text"],
                    "description": "Composite text combining key trial information for embedding",
                    "moduleConfig": {"text2vec-openai": {"skip": False}},
                },
                # Metadata
                {
                    "name": "dataSource",
                    "dataType": ["text"],
                    "description": "Data source (e.g., ClinicalTrials.gov)",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
                {
                    "name": "lastSyncedAt",
                    "dataType": ["date"],
                    "description": "Last time data was synced",
                    "moduleConfig": {"text2vec-openai": {"skip": True}},
                },
            ],
        }

        # Check if class already exists
        try:
            existing_schema = self.client.schema.get()
            class_names = [c["class"] for c in existing_schema.get("classes", [])]
            if "ClinicalTrial" not in class_names:
                self.client.schema.create_class(schema)
                logger.info("Created ClinicalTrial schema in Weaviate")
            else:
                logger.info("ClinicalTrial schema already exists")
        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
            raise

    def add_trial(self, trial_data: dict) -> str:
        """
        Add a trial to the vector store

        Args:
            trial_data: Dictionary containing trial information

        Returns:
            UUID of the created object
        """
        try:
            result = self.client.data_object.create(
                data_object=trial_data, class_name="ClinicalTrial"
            )
            logger.info(f"Added trial {trial_data.get('nctId')} to vector store")
            return result
        except Exception as e:
            logger.error(f"Error adding trial to vector store: {e}")
            raise

    def find_similar_trials(
        self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar trials using vector search

        Args:
            query: Search query text
            limit: Maximum number of results
            filters: Optional Weaviate filters

        Returns:
            List of similar trials with metadata
        """
        try:
            query_builder = (
                self.client.query.get(
                    "ClinicalTrial",
                    [
                        "nctId",
                        "title",
                        "phase",
                        "status",
                        "sponsor",
                        "conditions",
                        "interventions",
                        "outcomeClassification",
                        "enrollmentCount",
                        "startDate",
                        "completionDate",
                        "briefSummary",
                        "primaryOutcomes",
                    ],
                )
                .with_near_text({"concepts": [query]})
                .with_additional(["distance", "id"])
                .with_limit(limit)
            )

            if filters:
                query_builder = query_builder.with_where(filters)

            result = query_builder.do()
            return result.get("data", {}).get("Get", {}).get("ClinicalTrial", [])
        except Exception as e:
            logger.error(f"Error finding similar trials: {e}")
            raise

    def find_by_condition(
        self, condition: str, phase: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find trials by medical condition

        Args:
            condition: Medical condition to search for
            phase: Optional phase filter
            limit: Maximum number of results

        Returns:
            List of matching trials
        """
        try:
            where_filter = {
                "operator": "And",
                "operands": [
                    {
                        "path": ["conditions"],
                        "operator": "Like",
                        "valueText": f"*{condition}*",
                    }
                ],
            }

            if phase:
                where_filter["operands"].append(
                    {"path": ["phase"], "operator": "Equal", "valueText": phase}
                )

            result = (
                self.client.query.get(
                    "ClinicalTrial",
                    [
                        "nctId",
                        "title",
                        "phase",
                        "status",
                        "conditions",
                        "interventions",
                        "sponsor",
                        "enrollmentCount",
                        "outcomeClassification",
                        "briefSummary",
                    ],
                )
                .with_where(where_filter)
                .with_limit(limit)
                .do()
            )

            return result.get("data", {}).get("Get", {}).get("ClinicalTrial", [])
        except Exception as e:
            logger.error(f"Error finding trials by condition: {e}")
            raise

    def find_successful_trials(
        self,
        condition: Optional[str] = None,
        phase: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Find successful trials (outcome classified as Success)

        Args:
            condition: Optional condition filter
            phase: Optional phase filter
            limit: Maximum number of results

        Returns:
            List of successful trials
        """
        try:
            where_operands = [
                {
                    "path": ["outcomeClassification"],
                    "operator": "Equal",
                    "valueText": "Success",
                }
            ]

            if condition:
                where_operands.append(
                    {
                        "path": ["conditions"],
                        "operator": "Like",
                        "valueText": f"*{condition}*",
                    }
                )

            if phase:
                where_operands.append(
                    {"path": ["phase"], "operator": "Equal", "valueText": phase}
                )

            where_filter = {"operator": "And", "operands": where_operands}

            result = (
                self.client.query.get(
                    "ClinicalTrial",
                    [
                        "nctId",
                        "title",
                        "phase",
                        "conditions",
                        "interventions",
                        "sponsor",
                        "enrollmentCount",
                        "primaryOutcomes",
                        "briefSummary",
                        "studyDesign",
                    ],
                )
                .with_where(where_filter)
                .with_limit(limit)
                .do()
            )

            return result.get("data", {}).get("Get", {}).get("ClinicalTrial", [])
        except Exception as e:
            logger.error(f"Error finding successful trials: {e}")
            raise

    def hybrid_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        alpha: float = 0.5,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining keyword and vector search

        Args:
            query: Search query
            filters: Optional filters
            alpha: Balance between keyword (0) and vector (1) search
            limit: Maximum number of results

        Returns:
            List of matching trials
        """
        try:
            query_builder = (
                self.client.query.get(
                    "ClinicalTrial",
                    [
                        "nctId",
                        "title",
                        "phase",
                        "status",
                        "conditions",
                        "interventions",
                        "sponsor",
                        "outcomeClassification",
                        "enrollmentCount",
                        "briefSummary",
                        "primaryOutcomes",
                    ],
                )
                .with_hybrid(query=query, alpha=alpha)
                .with_additional(["score", "id"])
                .with_limit(limit)
            )

            if filters:
                query_builder = query_builder.with_where(filters)

            result = query_builder.do()
            return result.get("data", {}).get("Get", {}).get("ClinicalTrial", [])
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            raise

    def find_by_sponsor(
        self, sponsor: str, phase: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find trials by sponsor

        Args:
            sponsor: Sponsor name or partial name
            phase: Optional phase filter
            limit: Maximum number of results

        Returns:
            List of matching trials
        """
        try:
            where_operands = [
                {"path": ["sponsor"], "operator": "Like", "valueText": f"*{sponsor}*"}
            ]

            if phase:
                where_operands.append(
                    {"path": ["phase"], "operator": "Equal", "valueText": phase}
                )

            where_filter = {"operator": "And", "operands": where_operands}

            result = (
                self.client.query.get(
                    "ClinicalTrial",
                    [
                        "nctId",
                        "title",
                        "phase",
                        "status",
                        "sponsor",
                        "conditions",
                        "interventions",
                        "enrollmentCount",
                        "startDate",
                        "completionDate",
                        "outcomeClassification",
                    ],
                )
                .with_where(where_filter)
                .with_limit(limit)
                .do()
            )

            return result.get("data", {}).get("Get", {}).get("ClinicalTrial", [])
        except Exception as e:
            logger.error(f"Error finding trials by sponsor: {e}")
            raise

    def find_recent_trials(
        self, days: int = 30, status: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find recently updated trials

        Args:
            days: Number of days to look back
            status: Optional status filter
            limit: Maximum number of results

        Returns:
            List of recent trials
        """
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

            where_operands = [
                {
                    "path": ["lastUpdateDate"],
                    "operator": "GreaterThanEqual",
                    "valueDate": cutoff_date,
                }
            ]

            if status:
                where_operands.append(
                    {"path": ["status"], "operator": "Equal", "valueText": status}
                )

            where_filter = {"operator": "And", "operands": where_operands}

            result = (
                self.client.query.get(
                    "ClinicalTrial",
                    [
                        "nctId",
                        "title",
                        "phase",
                        "status",
                        "conditions",
                        "interventions",
                        "sponsor",
                        "lastUpdateDate",
                        "briefSummary",
                    ],
                )
                .with_where(where_filter)
                .with_limit(limit)
                .do()
            )

            return result.get("data", {}).get("Get", {}).get("ClinicalTrial", [])
        except Exception as e:
            logger.error(f"Error finding recent trials: {e}")
            raise

    def get_trial_by_nct_id(self, nct_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific trial by NCT ID

        Args:
            nct_id: NCT identifier

        Returns:
            Trial data or None if not found
        """
        try:
            result = (
                self.client.query.get(
                    "ClinicalTrial",
                    [
                        "nctId",
                        "title",
                        "phase",
                        "status",
                        "studyType",
                        "conditions",
                        "interventions",
                        "interventionType",
                        "sponsor",
                        "sponsorType",
                        "collaborators",
                        "startDate",
                        "completionDate",
                        "primaryCompletionDate",
                        "enrollmentCount",
                        "enrollmentType",
                        "eligibilityCriteria",
                        "sex",
                        "minimumAge",
                        "maximumAge",
                        "primaryOutcomes",
                        "secondaryOutcomes",
                        "outcomeClassification",
                        "hasResults",
                        "locationCountries",
                        "locationFacilities",
                        "studyDesign",
                        "armCount",
                        "briefSummary",
                        "detailedDescription",
                        "lastUpdateDate",
                    ],
                )
                .with_where(
                    {"path": ["nctId"], "operator": "Equal", "valueText": nct_id}
                )
                .with_limit(1)
                .do()
            )

            trials = result.get("data", {}).get("Get", {}).get("ClinicalTrial", [])
            return trials[0] if trials else None
        except Exception as e:
            logger.error(f"Error getting trial by NCT ID: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the trials in the vector store

        Returns:
            Dictionary with statistics
        """
        try:
            # Get total count
            total_result = (
                self.client.query.aggregate("ClinicalTrial").with_meta_count().do()
            )

            total_count = (
                total_result.get("data", {})
                .get("Aggregate", {})
                .get("ClinicalTrial", [{}])[0]
                .get("meta", {})
                .get("count", 0)
            )

            return {
                "total_trials": total_count,
                "last_updated": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"total_trials": 0, "error": str(e)}
