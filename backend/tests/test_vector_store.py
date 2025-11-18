"""
Tests for the clinical trial vector store
"""

import pytest
from unittest.mock import Mock, patch
from app.rag.vector_store import TrialVectorStore


class TestTrialVectorStore:
    """Test suite for TrialVectorStore"""

    @pytest.fixture
    def mock_weaviate_client(self):
        """Create a mock Weaviate client"""
        with patch("app.rag.vector_store.weaviate.Client") as mock_client:
            mock_instance = Mock()
            mock_client.return_value = mock_instance

            # Mock schema methods
            mock_instance.schema.get.return_value = {"classes": []}
            mock_instance.schema.create_class = Mock()

            yield mock_instance

    @pytest.fixture
    def vector_store(self, mock_weaviate_client):
        """Create a TrialVectorStore instance with mocked client"""
        return TrialVectorStore()

    def test_init_schema(self, vector_store, mock_weaviate_client):
        """Test schema initialization"""
        # Verify schema was created
        mock_weaviate_client.schema.create_class.assert_called_once()

        # Check schema structure
        call_args = mock_weaviate_client.schema.create_class.call_args[0][0]
        assert call_args["class"] == "ClinicalTrial"
        assert "properties" in call_args
        assert len(call_args["properties"]) > 0

    def test_add_trial(self, vector_store, mock_weaviate_client):
        """Test adding a trial to the vector store"""
        trial_data = {
            "nctId": "NCT00000001",
            "title": "Test Trial",
            "phase": "Phase 3",
            "conditions": ["Cancer"],
            "interventions": ["Drug A"],
        }

        mock_weaviate_client.data_object.create.return_value = "uuid-123"

        result = vector_store.add_trial(trial_data)

        mock_weaviate_client.data_object.create.assert_called_once_with(
            data_object=trial_data, class_name="ClinicalTrial"
        )
        assert result == "uuid-123"

    def test_find_similar_trials(self, vector_store, mock_weaviate_client):
        """Test finding similar trials"""
        mock_query = Mock()
        mock_weaviate_client.query = mock_query

        # Set up the query chain
        mock_get = Mock()
        mock_near_text = Mock()
        mock_additional = Mock()
        mock_limit = Mock()

        mock_query.get.return_value = mock_get
        mock_get.with_near_text.return_value = mock_near_text
        mock_near_text.with_additional.return_value = mock_additional
        mock_additional.with_limit.return_value = mock_limit

        # Mock result
        mock_limit.do.return_value = {
            "data": {
                "Get": {
                    "ClinicalTrial": [
                        {
                            "nctId": "NCT00000001",
                            "title": "Similar Trial",
                            "phase": "Phase 3",
                        }
                    ]
                }
            }
        }

        results = vector_store.find_similar_trials("cancer treatment", limit=5)

        assert len(results) == 1
        assert results[0]["nctId"] == "NCT00000001"
        mock_limit.do.assert_called_once()

    def test_find_by_condition(self, vector_store, mock_weaviate_client):
        """Test finding trials by condition"""
        mock_query = Mock()
        mock_weaviate_client.query = mock_query

        mock_get = Mock()
        mock_where = Mock()
        mock_limit = Mock()

        mock_query.get.return_value = mock_get
        mock_get.with_where.return_value = mock_where
        mock_where.with_limit.return_value = mock_limit

        mock_limit.do.return_value = {
            "data": {
                "Get": {
                    "ClinicalTrial": [
                        {"nctId": "NCT00000001", "conditions": ["Cancer"]}
                    ]
                }
            }
        }

        results = vector_store.find_by_condition("Cancer")

        assert len(results) == 1
        assert "Cancer" in results[0]["conditions"]

    def test_find_successful_trials(self, vector_store, mock_weaviate_client):
        """Test finding successful trials"""
        mock_query = Mock()
        mock_weaviate_client.query = mock_query

        mock_get = Mock()
        mock_where = Mock()
        mock_limit = Mock()

        mock_query.get.return_value = mock_get
        mock_get.with_where.return_value = mock_where
        mock_where.with_limit.return_value = mock_limit

        mock_limit.do.return_value = {
            "data": {
                "Get": {
                    "ClinicalTrial": [
                        {"nctId": "NCT00000001", "outcomeClassification": "Success"}
                    ]
                }
            }
        }

        results = vector_store.find_successful_trials(condition="Cancer")

        assert len(results) == 1
        assert results[0]["outcomeClassification"] == "Success"

    def test_get_trial_by_nct_id(self, vector_store, mock_weaviate_client):
        """Test getting a specific trial by NCT ID"""
        mock_query = Mock()
        mock_weaviate_client.query = mock_query

        mock_get = Mock()
        mock_where = Mock()
        mock_limit = Mock()

        mock_query.get.return_value = mock_get
        mock_get.with_where.return_value = mock_where
        mock_where.with_limit.return_value = mock_limit

        mock_limit.do.return_value = {
            "data": {
                "Get": {
                    "ClinicalTrial": [
                        {"nctId": "NCT00000001", "title": "Specific Trial"}
                    ]
                }
            }
        }

        result = vector_store.get_trial_by_nct_id("NCT00000001")

        assert result is not None
        assert result["nctId"] == "NCT00000001"

    def test_get_trial_by_nct_id_not_found(self, vector_store, mock_weaviate_client):
        """Test getting a trial that doesn't exist"""
        mock_query = Mock()
        mock_weaviate_client.query = mock_query

        mock_get = Mock()
        mock_where = Mock()
        mock_limit = Mock()

        mock_query.get.return_value = mock_get
        mock_get.with_where.return_value = mock_where
        mock_where.with_limit.return_value = mock_limit

        mock_limit.do.return_value = {"data": {"Get": {"ClinicalTrial": []}}}

        result = vector_store.get_trial_by_nct_id("NCT99999999")

        assert result is None
