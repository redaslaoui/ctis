"""
Data processing pipeline for clinical trial data
Handles cleaning, normalization, and transformation
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TrialDataProcessor:
    """Process and normalize clinical trial data from ClinicalTrials.gov API"""

    # Outcome classification keywords
    SUCCESS_KEYWORDS = [
        "met primary endpoint",
        "statistically significant",
        "positive results",
        "approved",
        "efficacy demonstrated",
    ]

    FAILURE_KEYWORDS = [
        "failed to meet",
        "not statistically significant",
        "negative results",
        "discontinued for futility",
        "insufficient efficacy",
    ]

    TERMINATED_STATUSES = ["TERMINATED", "WITHDRAWN", "SUSPENDED"]

    def __init__(self):
        """Initialize the data processor"""
        pass

    def extract_field(
        self, data: Dict[str, Any], path: str, default: Any = None
    ) -> Any:
        """
        Safely extract a nested field from the API response

        Args:
            data: Source data dictionary
            path: Dot-separated path to the field (e.g., "protocolSection.identificationModule.nctId")
            default: Default value if field not found

        Returns:
            Extracted value or default
        """
        keys = path.split(".")
        current = data

        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return default

            if current is None:
                return default

        return current if current is not None else default

    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parse and normalize date strings to ISO format

        Args:
            date_str: Date string in various formats

        Returns:
            ISO formatted date string or None
        """
        if not date_str:
            return None

        # Common date formats from ClinicalTrials.gov
        date_formats = [
            "%Y-%m-%d",
            "%B %Y",  # January 2020
            "%B %d, %Y",  # January 1, 2020
            "%Y",  # 2020
        ]

        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            except (ValueError, TypeError):
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def classify_outcome(
        self, status: str, results_text: Optional[str] = None, has_results: bool = False
    ) -> str:
        """
        Classify trial outcome based on status and results

        Args:
            status: Trial status
            results_text: Results description text
            has_results: Whether results have been posted

        Returns:
            Classified outcome: "Success", "Failure", "Terminated", or "Unknown"
        """
        # Check if terminated
        if status.upper() in self.TERMINATED_STATUSES:
            return "Terminated"

        # If no results posted, classification is unknown
        if not has_results or not results_text:
            return "Unknown"

        results_lower = results_text.lower()

        # Check for success indicators
        for keyword in self.SUCCESS_KEYWORDS:
            if keyword in results_lower:
                return "Success"

        # Check for failure indicators
        for keyword in self.FAILURE_KEYWORDS:
            if keyword in results_lower:
                return "Failure"

        return "Unknown"

    def extract_sponsor_info(self, protocol_section: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract sponsor information

        Args:
            protocol_section: Protocol section from API response

        Returns:
            Dictionary with sponsor and collaborator info
        """
        sponsor_module = protocol_section.get("sponsorCollaboratorsModule", {})

        lead_sponsor = sponsor_module.get("leadSponsor", {})
        sponsor_name = lead_sponsor.get("name", "Unknown")
        sponsor_class = lead_sponsor.get("class", "Unknown")

        collaborators = []
        if "collaborators" in sponsor_module:
            collaborators = [
                collab.get("name")
                for collab in sponsor_module["collaborators"]
                if collab.get("name")
            ]

        return {
            "sponsor": sponsor_name,
            "sponsorType": sponsor_class,
            "collaborators": collaborators,
        }

    def extract_conditions(self, protocol_section: Dict[str, Any]) -> List[str]:
        """
        Extract conditions/diseases being studied

        Args:
            protocol_section: Protocol section from API response

        Returns:
            List of condition names
        """
        conditions_module = protocol_section.get("conditionsModule", {})
        conditions = conditions_module.get("conditions", [])
        return conditions if conditions else []

    def extract_interventions(self, protocol_section: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract intervention information

        Args:
            protocol_section: Protocol section from API response

        Returns:
            Dictionary with interventions and intervention type
        """
        arms_module = protocol_section.get("armsInterventionsModule", {})
        interventions = arms_module.get("interventions", [])

        intervention_names = []
        intervention_type = "Unknown"

        if interventions:
            intervention_names = [
                interv.get("name") for interv in interventions if interv.get("name")
            ]

            # Get the type from the first intervention
            if interventions[0].get("type"):
                intervention_type = interventions[0]["type"]

        return {
            "interventions": intervention_names,
            "interventionType": intervention_type,
        }

    def extract_outcomes(self, protocol_section: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract outcome measures

        Args:
            protocol_section: Protocol section from API response

        Returns:
            Dictionary with primary and secondary outcomes
        """
        outcomes_module = protocol_section.get("outcomesModule", {})

        primary_outcomes = []
        if "primaryOutcomes" in outcomes_module:
            primary_outcomes = [
                outcome.get("measure")
                for outcome in outcomes_module["primaryOutcomes"]
                if outcome.get("measure")
            ]

        secondary_outcomes = []
        if "secondaryOutcomes" in outcomes_module:
            secondary_outcomes = [
                outcome.get("measure")
                for outcome in outcomes_module["secondaryOutcomes"]
                if outcome.get("measure")
            ]

        return {
            "primaryOutcomes": primary_outcomes,
            "secondaryOutcomes": secondary_outcomes,
        }

    def extract_eligibility(self, protocol_section: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract eligibility criteria

        Args:
            protocol_section: Protocol section from API response

        Returns:
            Dictionary with eligibility information
        """
        eligibility_module = protocol_section.get("eligibilityModule", {})

        return {
            "eligibilityCriteria": eligibility_module.get("eligibilityCriteria", ""),
            "sex": eligibility_module.get("sex", "All"),
            "minimumAge": eligibility_module.get("minimumAge", "N/A"),
            "maximumAge": eligibility_module.get("maximumAge", "N/A"),
        }

    def extract_locations(self, protocol_section: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract location information

        Args:
            protocol_section: Protocol section from API response

        Returns:
            Dictionary with countries and facilities
        """
        locations_module = protocol_section.get("contactsLocationsModule", {})
        locations = locations_module.get("locations", [])

        countries = set()
        facilities = []

        for location in locations:
            if location.get("country"):
                countries.add(location["country"])
            if location.get("facility"):
                facilities.append(location["facility"])

        return {"locationCountries": list(countries), "locationFacilities": facilities}

    def create_composite_text(self, trial_data: Dict[str, Any]) -> str:
        """
        Create composite text for rich embeddings

        Args:
            trial_data: Processed trial data

        Returns:
            Combined text string for vectorization
        """
        parts = []

        # Add title
        if trial_data.get("title"):
            parts.append(f"Title: {trial_data['title']}")

        # Add phase and status
        if trial_data.get("phase"):
            parts.append(f"Phase: {trial_data['phase']}")

        # Add conditions
        if trial_data.get("conditions"):
            conditions_str = ", ".join(trial_data["conditions"])
            parts.append(f"Conditions: {conditions_str}")

        # Add interventions
        if trial_data.get("interventions"):
            interventions_str = ", ".join(trial_data["interventions"])
            parts.append(f"Interventions: {interventions_str}")

        # Add brief summary
        if trial_data.get("briefSummary"):
            parts.append(f"Summary: {trial_data['briefSummary']}")

        # Add primary outcomes
        if trial_data.get("primaryOutcomes"):
            outcomes_str = "; ".join(trial_data["primaryOutcomes"])
            parts.append(f"Primary Outcomes: {outcomes_str}")

        return " | ".join(parts)

    def process_study(self, raw_study: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a raw study from the API into the format expected by Weaviate

        Args:
            raw_study: Raw study data from ClinicalTrials.gov API

        Returns:
            Processed and normalized trial data
        """
        try:
            protocol_section = raw_study.get("protocolSection", {})

            # Basic identification
            identification_module = protocol_section.get("identificationModule", {})
            nct_id = identification_module.get("nctId")
            title = identification_module.get(
                "officialTitle"
            ) or identification_module.get("briefTitle", "")

            # Description
            description_module = protocol_section.get("descriptionModule", {})
            brief_summary = description_module.get("briefSummary", "")
            detailed_description = description_module.get("detailedDescription", "")

            # Design
            design_module = protocol_section.get("designModule", {})
            phases = design_module.get("phases", [])
            phase = phases[0] if phases else "N/A"
            study_type = design_module.get("studyType", "Unknown")

            # Status
            status_module = protocol_section.get("statusModule", {})
            status = status_module.get("overallStatus", "Unknown")
            has_results = raw_study.get("hasResults", False)

            # Dates
            start_date = self.parse_date(
                status_module.get("startDateStruct", {}).get("date")
            )
            completion_date = self.parse_date(
                status_module.get("completionDateStruct", {}).get("date")
            )
            primary_completion_date = self.parse_date(
                status_module.get("primaryCompletionDateStruct", {}).get("date")
            )
            last_update_date = self.parse_date(
                status_module.get("lastUpdatePostDateStruct", {}).get("date")
            )

            # Enrollment
            enrollment_info = design_module.get("enrollmentInfo", {})
            enrollment_count = enrollment_info.get("count")
            enrollment_type = enrollment_info.get("type", "Anticipated")

            # Study design
            study_design_parts = []
            if design_module.get("designInfo"):
                design_info = design_module["designInfo"]
                if design_info.get("allocation"):
                    study_design_parts.append(
                        f"Allocation: {design_info['allocation']}"
                    )
                if design_info.get("interventionModel"):
                    study_design_parts.append(
                        f"Model: {design_info['interventionModel']}"
                    )
                if design_info.get("primaryPurpose"):
                    study_design_parts.append(
                        f"Purpose: {design_info['primaryPurpose']}"
                    )

            study_design = "; ".join(study_design_parts) if study_design_parts else ""

            # Extract complex fields
            sponsor_info = self.extract_sponsor_info(protocol_section)
            conditions = self.extract_conditions(protocol_section)
            intervention_info = self.extract_interventions(protocol_section)
            outcome_info = self.extract_outcomes(protocol_section)
            eligibility_info = self.extract_eligibility(protocol_section)
            location_info = self.extract_locations(protocol_section)

            # Classify outcome
            results_text = detailed_description or brief_summary
            outcome_classification = self.classify_outcome(
                status, results_text, has_results
            )

            # Arm count
            arms_module = protocol_section.get("armsInterventionsModule", {})
            arm_count = len(arms_module.get("armGroups", []))

            # Build processed trial data
            trial_data = {
                "nctId": nct_id,
                "title": title,
                "briefSummary": brief_summary,
                "detailedDescription": detailed_description,
                "phase": phase,
                "status": status,
                "studyType": study_type,
                "conditions": conditions,
                "interventions": intervention_info["interventions"],
                "interventionType": intervention_info["interventionType"],
                "sponsor": sponsor_info["sponsor"],
                "sponsorType": sponsor_info["sponsorType"],
                "collaborators": sponsor_info["collaborators"],
                "startDate": start_date,
                "completionDate": completion_date,
                "primaryCompletionDate": primary_completion_date,
                "lastUpdateDate": last_update_date,
                "enrollmentCount": enrollment_count,
                "enrollmentType": enrollment_type,
                "eligibilityCriteria": eligibility_info["eligibilityCriteria"],
                "sex": eligibility_info["sex"],
                "minimumAge": eligibility_info["minimumAge"],
                "maximumAge": eligibility_info["maximumAge"],
                "primaryOutcomes": outcome_info["primaryOutcomes"],
                "secondaryOutcomes": outcome_info["secondaryOutcomes"],
                "outcomeClassification": outcome_classification,
                "hasResults": has_results,
                "locationCountries": location_info["locationCountries"],
                "locationFacilities": location_info["locationFacilities"],
                "studyDesign": study_design,
                "armCount": arm_count,
                "dataSource": "ClinicalTrials.gov",
                "lastSyncedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

            # Create composite text
            trial_data["compositeText"] = self.create_composite_text(trial_data)

            logger.debug(f"Processed trial {nct_id}")
            return trial_data

        except Exception as e:
            logger.error(f"Error processing study: {e}")
            raise
