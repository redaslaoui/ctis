"""
Tests for the clinical trial data processor
"""

import pytest
from datetime import datetime
from app.services.data_processor import TrialDataProcessor


class TestTrialDataProcessor:
    """Test suite for TrialDataProcessor"""

    @pytest.fixture
    def processor(self):
        """Create a TrialDataProcessor instance"""
        return TrialDataProcessor()

    def test_extract_field(self, processor):
        """Test nested field extraction"""
        data = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000001"
                }
            }
        }

        result = processor.extract_field(data, "protocolSection.identificationModule.nctId")
        assert result == "NCT00000001"

    def test_extract_field_with_default(self, processor):
        """Test field extraction with default value"""
        data = {}

        result = processor.extract_field(data, "missing.field", default="N/A")
        assert result == "N/A"

    def test_parse_date_iso_format(self, processor):
        """Test parsing ISO date format"""
        date_str = "2023-01-15"
        result = processor.parse_date(date_str)

        assert result is not None
        assert "2023-01-15" in result

    def test_parse_date_month_year(self, processor):
        """Test parsing month-year format"""
        date_str = "January 2023"
        result = processor.parse_date(date_str)

        assert result is not None
        assert "2023-01" in result

    def test_parse_date_invalid(self, processor):
        """Test parsing invalid date"""
        date_str = "invalid-date"
        result = processor.parse_date(date_str)

        assert result is None

    def test_classify_outcome_terminated(self, processor):
        """Test outcome classification for terminated trials"""
        result = processor.classify_outcome("TERMINATED")

        assert result == "Terminated"

    def test_classify_outcome_success(self, processor):
        """Test outcome classification for successful trials"""
        results_text = "The trial met primary endpoint with statistically significant results"
        result = processor.classify_outcome("COMPLETED", results_text, has_results=True)

        assert result == "Success"

    def test_classify_outcome_failure(self, processor):
        """Test outcome classification for failed trials"""
        results_text = "The trial failed to meet the primary endpoint"
        result = processor.classify_outcome("COMPLETED", results_text, has_results=True)

        assert result == "Failure"

    def test_classify_outcome_unknown(self, processor):
        """Test outcome classification for unknown outcomes"""
        result = processor.classify_outcome("COMPLETED", has_results=False)

        assert result == "Unknown"

    def test_extract_sponsor_info(self, processor):
        """Test sponsor information extraction"""
        protocol_section = {
            "sponsorCollaboratorsModule": {
                "leadSponsor": {
                    "name": "Pharma Corp",
                    "class": "Industry"
                },
                "collaborators": [
                    {"name": "University Hospital"},
                    {"name": "Research Institute"}
                ]
            }
        }

        result = processor.extract_sponsor_info(protocol_section)

        assert result["sponsor"] == "Pharma Corp"
        assert result["sponsorType"] == "Industry"
        assert len(result["collaborators"]) == 2
        assert "University Hospital" in result["collaborators"]

    def test_extract_conditions(self, processor):
        """Test conditions extraction"""
        protocol_section = {
            "conditionsModule": {
                "conditions": ["Cancer", "Solid Tumor"]
            }
        }

        result = processor.extract_conditions(protocol_section)

        assert len(result) == 2
        assert "Cancer" in result
        assert "Solid Tumor" in result

    def test_extract_interventions(self, processor):
        """Test interventions extraction"""
        protocol_section = {
            "armsInterventionsModule": {
                "interventions": [
                    {
                        "name": "Drug A",
                        "type": "Drug"
                    },
                    {
                        "name": "Placebo",
                        "type": "Other"
                    }
                ]
            }
        }

        result = processor.extract_interventions(protocol_section)

        assert len(result["interventions"]) == 2
        assert "Drug A" in result["interventions"]
        assert result["interventionType"] == "Drug"

    def test_extract_outcomes(self, processor):
        """Test outcomes extraction"""
        protocol_section = {
            "outcomesModule": {
                "primaryOutcomes": [
                    {"measure": "Overall Survival"},
                    {"measure": "Progression-Free Survival"}
                ],
                "secondaryOutcomes": [
                    {"measure": "Quality of Life"}
                ]
            }
        }

        result = processor.extract_outcomes(protocol_section)

        assert len(result["primaryOutcomes"]) == 2
        assert "Overall Survival" in result["primaryOutcomes"]
        assert len(result["secondaryOutcomes"]) == 1
        assert "Quality of Life" in result["secondaryOutcomes"]

    def test_extract_eligibility(self, processor):
        """Test eligibility extraction"""
        protocol_section = {
            "eligibilityModule": {
                "eligibilityCriteria": "Age 18-65, diagnosis confirmed",
                "sex": "All",
                "minimumAge": "18 Years",
                "maximumAge": "65 Years"
            }
        }

        result = processor.extract_eligibility(protocol_section)

        assert result["eligibilityCriteria"] == "Age 18-65, diagnosis confirmed"
        assert result["sex"] == "All"
        assert result["minimumAge"] == "18 Years"
        assert result["maximumAge"] == "65 Years"

    def test_extract_locations(self, processor):
        """Test locations extraction"""
        protocol_section = {
            "contactsLocationsModule": {
                "locations": [
                    {
                        "country": "United States",
                        "facility": "Mayo Clinic"
                    },
                    {
                        "country": "United States",
                        "facility": "Johns Hopkins"
                    },
                    {
                        "country": "Canada",
                        "facility": "Toronto General"
                    }
                ]
            }
        }

        result = processor.extract_locations(protocol_section)

        assert len(result["locationCountries"]) == 2
        assert "United States" in result["locationCountries"]
        assert "Canada" in result["locationCountries"]
        assert len(result["locationFacilities"]) == 3

    def test_create_composite_text(self, processor):
        """Test composite text creation"""
        trial_data = {
            "title": "Test Trial",
            "phase": "Phase 3",
            "conditions": ["Cancer"],
            "interventions": ["Drug A"],
            "briefSummary": "Testing drug A for cancer",
            "primaryOutcomes": ["Overall Survival"]
        }

        result = processor.create_composite_text(trial_data)

        assert "Test Trial" in result
        assert "Phase 3" in result
        assert "Cancer" in result
        assert "Drug A" in result
        assert "Testing drug A for cancer" in result
        assert "Overall Survival" in result

    def test_process_study_basic(self, processor):
        """Test basic study processing"""
        raw_study = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000001",
                    "officialTitle": "Test Clinical Trial"
                },
                "descriptionModule": {
                    "briefSummary": "Brief summary of the trial"
                },
                "designModule": {
                    "phases": ["PHASE3"],
                    "studyType": "Interventional"
                },
                "statusModule": {
                    "overallStatus": "COMPLETED"
                }
            },
            "hasResults": False
        }

        result = processor.process_study(raw_study)

        assert result["nctId"] == "NCT00000001"
        assert result["title"] == "Test Clinical Trial"
        assert result["phase"] == "PHASE3"
        assert result["status"] == "COMPLETED"
        assert result["studyType"] == "Interventional"
        assert result["dataSource"] == "ClinicalTrials.gov"
        assert "compositeText" in result
