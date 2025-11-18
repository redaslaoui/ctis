from app.services.celery_app import celery_app
from app.services.clinicaltrials_api import ClinicalTrialsAPIClient
from app.services.data_processor import TrialDataProcessor
from app.rag.vector_store import TrialVectorStore
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def ingest_trials_batch(
    self,
    query: Optional[str] = None,
    max_results: int = 1000,
    filters: Optional[Dict[str, Any]] = None,
):
    """
    Background task to ingest a batch of trials from ClinicalTrials.gov

    Args:
        query: Optional search query
        max_results: Maximum number of trials to ingest
        filters: Optional filters for the search
    """
    try:
        api_client = ClinicalTrialsAPIClient()
        processor = TrialDataProcessor()
        vector_store = TrialVectorStore()

        total_processed = 0
        total_added = 0
        total_skipped = 0
        total_errors = 0

        logger.info(
            f"Starting batch ingestion: query={query}, max_results={max_results}"
        )

        # Fetch studies from API
        studies = api_client.search_studies(
            query=query, filters=filters, max_results=max_results
        )

        for study in studies:
            try:
                # Process the study
                processed_data = processor.process_study(study)
                nct_id = processed_data.get("nctId")

                if not nct_id:
                    logger.warning("Study missing NCT ID, skipping")
                    total_skipped += 1
                    continue

                # Check for duplicates in vector store
                existing_trials = vector_store.find_similar_trials(
                    query=nct_id,
                    limit=1,
                    filters={
                        "path": ["nctId"],
                        "operator": "Equal",
                        "valueText": nct_id,
                    },
                )

                if existing_trials:
                    logger.debug(f"Trial {nct_id} already exists, skipping")
                    total_skipped += 1
                else:
                    # Add to vector store
                    vector_store.add_trial(processed_data)
                    total_added += 1
                    logger.info(f"Added trial {nct_id} to vector store")

                total_processed += 1

                # Update progress every 10 trials
                if total_processed % 10 == 0:
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "processed": total_processed,
                            "added": total_added,
                            "skipped": total_skipped,
                            "errors": total_errors,
                        },
                    )

            except Exception as e:
                logger.error(f"Error processing study: {e}")
                total_errors += 1
                continue

        logger.info(
            f"Batch ingestion completed: processed={total_processed}, "
            f"added={total_added}, skipped={total_skipped}, errors={total_errors}"
        )

        return {
            "status": "completed",
            "processed": total_processed,
            "added": total_added,
            "skipped": total_skipped,
            "errors": total_errors,
        }

    except Exception as e:
        logger.error(f"Batch ingestion failed: {e}")
        raise


@celery_app.task
def sync_trials_daily():
    """
    Daily task to sync trials updated in the last 24 hours
    """
    try:
        api_client = ClinicalTrialsAPIClient()
        processor = TrialDataProcessor()
        vector_store = TrialVectorStore()

        # Get trials updated in last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)

        total_synced = 0
        total_errors = 0

        logger.info(f"Starting daily sync for trials updated since {yesterday}")

        studies = api_client.get_studies_updated_since(yesterday)

        for study in studies:
            try:
                processed_data = processor.process_study(study)
                nct_id = processed_data.get("nctId")

                if not nct_id:
                    continue

                # Add or update trial
                vector_store.add_trial(processed_data)
                total_synced += 1

                logger.debug(f"Synced trial {nct_id}")

            except Exception as e:
                logger.error(f"Error syncing study: {e}")
                total_errors += 1
                continue

        logger.info(
            f"Daily sync completed: synced={total_synced}, errors={total_errors}"
        )

        return {"status": "completed", "synced": total_synced, "errors": total_errors}

    except Exception as e:
        logger.error(f"Daily sync failed: {e}")
        raise


@celery_app.task
def sync_completed_trials_by_condition(condition: str, max_results: int = 500):
    """
    Sync completed trials for a specific condition

    Args:
        condition: Medical condition to filter by
        max_results: Maximum number of trials to sync
    """
    try:
        api_client = ClinicalTrialsAPIClient()
        processor = TrialDataProcessor()
        vector_store = TrialVectorStore()

        total_synced = 0

        logger.info(f"Syncing completed trials for condition: {condition}")

        studies = api_client.get_completed_trials(
            condition=condition, max_results=max_results
        )

        for study in studies:
            try:
                processed_data = processor.process_study(study)
                vector_store.add_trial(processed_data)
                total_synced += 1

            except Exception as e:
                logger.error(f"Error syncing study: {e}")
                continue

        logger.info(f"Synced {total_synced} completed trials for {condition}")

        return {"status": "completed", "condition": condition, "synced": total_synced}

    except Exception as e:
        logger.error(f"Failed to sync trials for condition {condition}: {e}")
        raise


@celery_app.task
def analyze_trial_risk(trial_id: int):
    """Background task to analyze trial risk using AI agents"""
    # TODO: Implement risk analysis logic using the agent
    pass


@celery_app.task
def monitor_trial_kpis(trial_id: int):
    """Background task to monitor trial KPIs"""
    # TODO: Implement monitoring logic
    pass
