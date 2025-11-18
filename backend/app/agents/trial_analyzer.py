from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from app.core.config import settings
from app.rag.retriever import ClinicalTrialRetriever, SuccessfulTrialRetriever
from app.rag.vector_store import TrialVectorStore
import logging
import json

logger = logging.getLogger(__name__)


class TrialAnalyzerAgent:
    """Agent responsible for analyzing clinical trials and predicting risk using RAG"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4", api_key=settings.OPENAI_API_KEY, temperature=0
        )

        self.vector_store = TrialVectorStore()
        self.retriever = ClinicalTrialRetriever(vector_store=self.vector_store, limit=5)
        self.success_retriever = SuccessfulTrialRetriever(
            vector_store=self.vector_store, limit=5
        )

    def _build_trial_context(self, trial_data: dict) -> str:
        """Build context string from trial data"""
        parts = []

        if trial_data.get("title"):
            parts.append(f"Title: {trial_data['title']}")

        if trial_data.get("phase"):
            parts.append(f"Phase: {trial_data['phase']}")

        if trial_data.get("condition"):
            parts.append(f"Condition: {trial_data['condition']}")

        if trial_data.get("intervention"):
            parts.append(f"Intervention: {trial_data['intervention']}")

        if trial_data.get("enrollment_target"):
            parts.append(f"Target Enrollment: {trial_data['enrollment_target']}")

        if trial_data.get("sponsor"):
            parts.append(f"Sponsor: {trial_data['sponsor']}")

        return "\n".join(parts)

    def analyze_trial(self, trial_data: dict) -> dict:
        """
        Analyze a clinical trial and predict failure risk using RAG

        Args:
            trial_data: Dictionary containing trial information

        Returns:
            Dictionary with risk score, confidence, and risk factors
        """
        try:
            # Build query for similar trials
            query_parts = []
            if trial_data.get("condition"):
                query_parts.append(trial_data["condition"])
            if trial_data.get("intervention"):
                query_parts.append(trial_data["intervention"])
            if trial_data.get("phase"):
                query_parts.append(f"Phase {trial_data['phase']}")

            query = " ".join(query_parts)

            # Retrieve similar trials
            similar_trials = self.retriever.get_relevant_documents(query)

            # Build context from similar trials
            context = "\n\n---\n\n".join([doc.page_content for doc in similar_trials])

            # Create trial context
            trial_context = self._build_trial_context(trial_data)

            # Risk analysis prompt
            risk_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an expert clinical trial risk analyst.

Analyze the provided trial and predict the risk of failure based on:
1. Similar historical trials and their outcomes
2. Trial design characteristics
3. Enrollment targets and feasibility
4. Sponsor track record
5. Phase-specific risk factors

Provide your analysis in the following JSON format:
{{
    "risk_score": <float between 0-1, where 1 is highest risk>,
    "confidence": <float between 0-1>,
    "risk_factors": [<list of specific risk factors>],
    "reasoning": "<brief explanation>"
}}""",
                    ),
                    (
                        "user",
                        """Current Trial:
{trial_context}

Similar Historical Trials:
{context}

Analyze the risk of failure for this trial.""",
                    ),
                ]
            )

            # Run analysis
            chain = risk_prompt | self.llm | StrOutputParser()

            response = chain.invoke(
                {"trial_context": trial_context, "context": context}
            )

            # Parse response
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse JSON response, returning default")
                result = {
                    "risk_score": 0.5,
                    "confidence": 0.3,
                    "risk_factors": ["Unable to parse detailed analysis"],
                    "reasoning": response,
                }

            logger.info(
                f"Risk analysis completed: risk_score={result.get('risk_score')}"
            )
            return result

        except Exception as e:
            logger.error(f"Error analyzing trial: {e}")
            return {
                "risk_score": 0.0,
                "confidence": 0.0,
                "risk_factors": [f"Error: {str(e)}"],
            }

    def recommend_optimizations(self, trial_data: dict) -> list:
        """
        Recommend optimizations based on successful patterns

        Args:
            trial_data: Dictionary containing trial information

        Returns:
            List of recommendations
        """
        try:
            # Get condition for finding successful trials
            condition = trial_data.get("condition", "")
            phase = trial_data.get("phase")

            # Update success retriever filters
            self.success_retriever.condition = condition
            self.success_retriever.phase = phase

            # Retrieve successful trials
            successful_trials = self.success_retriever.get_relevant_documents(condition)

            if not successful_trials:
                return ["No similar successful trials found for comparison"]

            # Build context from successful trials
            context = "\n\n---\n\n".join(
                [doc.page_content for doc in successful_trials]
            )

            # Create trial context
            trial_context = self._build_trial_context(trial_data)

            # Recommendation prompt
            rec_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an expert clinical trial consultant specializing in trial optimization.

Based on successful historical trials, provide specific, actionable recommendations to improve trial success.

Focus on:
1. Study design improvements
2. Enrollment strategies
3. Endpoint selection
4. Patient selection criteria
5. Site selection and management

Provide recommendations as a JSON array of strings.""",
                    ),
                    (
                        "user",
                        """Current Trial:
{trial_context}

Successful Similar Trials:
{context}

Provide specific optimization recommendations for this trial.""",
                    ),
                ]
            )

            # Run recommendation
            chain = rec_prompt | self.llm | StrOutputParser()

            response = chain.invoke(
                {"trial_context": trial_context, "context": context}
            )

            # Parse response
            try:
                recommendations = json.loads(response)
                if isinstance(recommendations, list):
                    return recommendations
                else:
                    return [response]
            except json.JSONDecodeError:
                # Split by newlines or numbered list
                lines = response.strip().split("\n")
                recommendations = [
                    line.strip("- ").strip("0123456789. ")
                    for line in lines
                    if line.strip()
                ]
                return recommendations[:10]  # Limit to top 10

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return [f"Error generating recommendations: {str(e)}"]
