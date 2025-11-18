"""
LangChain retriever integration for clinical trial vector store
"""

from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from app.rag.vector_store import TrialVectorStore
import logging

logger = logging.getLogger(__name__)


class ClinicalTrialRetriever(BaseRetriever):
    """LangChain retriever wrapping the Weaviate vector store"""

    vector_store: TrialVectorStore
    search_kwargs: Dict[str, Any] = {}

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, vector_store: Optional[TrialVectorStore] = None, **kwargs):
        """
        Initialize the retriever

        Args:
            vector_store: TrialVectorStore instance
            **kwargs: Additional search parameters
        """
        if vector_store is None:
            vector_store = TrialVectorStore()

        super().__init__(vector_store=vector_store, search_kwargs=kwargs)

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None
    ) -> List[Document]:
        """
        Get documents relevant to a query

        Args:
            query: Query string
            run_manager: Callback manager

        Returns:
            List of relevant documents
        """
        try:
            # Get search parameters
            limit = self.search_kwargs.get("limit", 10)
            filters = self.search_kwargs.get("filters")

            # Perform vector search
            trials = self.vector_store.find_similar_trials(
                query=query,
                limit=limit,
                filters=filters
            )

            # Convert to LangChain documents
            documents = []
            for trial in trials:
                # Create document content
                content_parts = []

                if trial.get("title"):
                    content_parts.append(f"Title: {trial['title']}")

                if trial.get("nctId"):
                    content_parts.append(f"NCT ID: {trial['nctId']}")

                if trial.get("phase"):
                    content_parts.append(f"Phase: {trial['phase']}")

                if trial.get("conditions"):
                    conditions_str = ", ".join(trial["conditions"])
                    content_parts.append(f"Conditions: {conditions_str}")

                if trial.get("interventions"):
                    interventions_str = ", ".join(trial["interventions"])
                    content_parts.append(f"Interventions: {interventions_str}")

                if trial.get("briefSummary"):
                    content_parts.append(f"Summary: {trial['briefSummary']}")

                if trial.get("primaryOutcomes"):
                    outcomes_str = "; ".join(trial["primaryOutcomes"])
                    content_parts.append(f"Primary Outcomes: {outcomes_str}")

                if trial.get("outcomeClassification"):
                    content_parts.append(f"Outcome: {trial['outcomeClassification']}")

                content = "\n".join(content_parts)

                # Create metadata
                metadata = {
                    "nct_id": trial.get("nctId"),
                    "phase": trial.get("phase"),
                    "status": trial.get("status"),
                    "sponsor": trial.get("sponsor"),
                    "enrollment_count": trial.get("enrollmentCount"),
                    "outcome_classification": trial.get("outcomeClassification")
                }

                # Add distance if available
                if trial.get("_additional", {}).get("distance"):
                    metadata["distance"] = trial["_additional"]["distance"]

                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)

            logger.info(f"Retrieved {len(documents)} documents for query: {query}")
            return documents

        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []


class SuccessfulTrialRetriever(BaseRetriever):
    """Specialized retriever for successful trials"""

    vector_store: TrialVectorStore
    condition: Optional[str] = None
    phase: Optional[str] = None
    limit: int = 10

    class Config:
        arbitrary_types_allowed = True

    def __init__(
        self,
        vector_store: Optional[TrialVectorStore] = None,
        condition: Optional[str] = None,
        phase: Optional[str] = None,
        limit: int = 10
    ):
        """
        Initialize the successful trial retriever

        Args:
            vector_store: TrialVectorStore instance
            condition: Optional condition filter
            phase: Optional phase filter
            limit: Maximum number of results
        """
        if vector_store is None:
            vector_store = TrialVectorStore()

        super().__init__(
            vector_store=vector_store,
            condition=condition,
            phase=phase,
            limit=limit
        )

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None
    ) -> List[Document]:
        """
        Get successful trial documents

        Args:
            query: Query string (used for condition if not set)
            run_manager: Callback manager

        Returns:
            List of successful trial documents
        """
        try:
            # Use query as condition if not set
            condition = self.condition or query

            # Find successful trials
            trials = self.vector_store.find_successful_trials(
                condition=condition,
                phase=self.phase,
                limit=self.limit
            )

            # Convert to documents
            documents = []
            for trial in trials:
                content_parts = [
                    f"NCT ID: {trial.get('nctId')}",
                    f"Title: {trial.get('title')}",
                    f"Phase: {trial.get('phase')}",
                    f"Conditions: {', '.join(trial.get('conditions', []))}",
                    f"Interventions: {', '.join(trial.get('interventions', []))}",
                    f"Study Design: {trial.get('studyDesign')}",
                    f"Enrollment: {trial.get('enrollmentCount')}",
                    f"Primary Outcomes: {'; '.join(trial.get('primaryOutcomes', []))}"
                ]

                content = "\n".join(content_parts)

                metadata = {
                    "nct_id": trial.get("nctId"),
                    "phase": trial.get("phase"),
                    "sponsor": trial.get("sponsor"),
                    "enrollment_count": trial.get("enrollmentCount")
                }

                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)

            logger.info(f"Retrieved {len(documents)} successful trials")
            return documents

        except Exception as e:
            logger.error(f"Error retrieving successful trials: {e}")
            return []
