"""Airflow task functions for SEC filing pipeline."""

import logging
import sys
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path so we can import dealminer
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dealminer.config.settings import (
    MONGODB_COLLECTION_NAME,
    MONGODB_CONNECTION_STRING,
    MONGODB_DATABASE_NAME,
    RAW_DATA_DIR,
    SUPPORTED_FORM_TYPES,
)
from dealminer.downloader.filing_discovery import FilingMetadata, discover_filings_for_date
from dealminer.downloader.filing_downloader import download_filing_with_manifest
from dealminer.parser import Form8KParser, get_parser
from dealminer.storage import (
    get_collection,
    get_database,
    get_mongodb_client,
    store_filings_batch,
)

logger = logging.getLogger(__name__)

# Target form types (excluding 8-K which needs special handling)
TARGET_FORM_TYPES = ["PREM14A", "SCTOT", "SC14D9", "S-4", "425"]

# Target items for Form 8-K
TARGET_8K_ITEMS = ["1.01", "2.01", "9.01"]


def _filing_metadata_to_dict(filing: FilingMetadata) -> Dict[str, Any]:
    """Convert FilingMetadata dataclass to dictionary for XCom.

    Args:
        filing: FilingMetadata object.

    Returns:
        Dictionary representation.
    """
    return {
        "cik": filing.cik,
        "company_name": filing.company_name,
        "form_type": filing.form_type,
        "date_filed": filing.date_filed,
        "file_name": filing.file_name,
        "accession_number": filing.accession_number,
    }


def discover_filings_task(target_date: str, **kwargs) -> List[Dict[str, Any]]:
    """Discover all target filings for a given date.

    Args:
        target_date: Date string in YYYY-MM-DD format.
        **kwargs: Airflow context (unused but required).

    Returns:
        List of filing metadata dictionaries (JSON-serializable).
    """
    logger.info(f"Discovering filings for date: {target_date}")

    try:
        filing_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {target_date}. Use YYYY-MM-DD")

    try:
        # Discover all target forms
        all_form_types = TARGET_FORM_TYPES + ["8-K", "8K"]
        filings, _ = discover_filings_for_date(
            filing_date=filing_date,
            form_types=all_form_types,
            save_index_file=False,
        )

        # Convert to dictionaries for XCom
        filing_dicts = [_filing_metadata_to_dict(f) for f in filings]

        logger.info(
            f"Discovered {len(filing_dicts)} filings for {target_date}"
        )

        return filing_dicts

    except FileNotFoundError:
        logger.warning(
            f"No index file found for {target_date} (likely weekend/holiday)"
        )
        return []


def download_target_forms_task(
    filing_list: List[Dict[str, Any]], **kwargs
) -> List[Dict[str, Any]]:
    """Download target forms (excluding 8-K).

    Args:
        filing_list: List of filing metadata dictionaries from discover task.
        **kwargs: Airflow context.

    Returns:
        List of dictionaries with filing metadata and downloaded file paths.
    """
    logger.info(f"Downloading target forms (excluding 8-K)")

    # Filter for non-8-K forms
    target_filings = [
        f for f in filing_list if f.get("form_type") in TARGET_FORM_TYPES
    ]

    if not target_filings:
        logger.info("No target forms to download")
        return []

    output_dir = RAW_DATA_DIR / "filings"
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded_filings = []

    for filing_dict in target_filings:
        try:
            # Convert dict back to FilingMetadata
            filing = FilingMetadata(
                cik=filing_dict["cik"],
                company_name=filing_dict["company_name"],
                form_type=filing_dict["form_type"],
                date_filed=filing_dict["date_filed"],
                file_name=filing_dict["file_name"],
                accession_number=filing_dict.get("accession_number"),
            )

            # Download filing
            downloaded_files = download_filing_with_manifest(
                filing_metadata=filing,
                output_dir=output_dir,
                download_exhibits=True,
                save_manifest=True,
            )

            downloaded_filings.append(
                {
                    "filing_metadata": filing_dict,
                    "downloaded_files": {
                        k: str(v) if isinstance(v, Path) else v
                        for k, v in downloaded_files.items()
                    },
                }
            )

            logger.info(
                f"Downloaded {filing.form_type} - {filing.company_name} "
                f"({filing.accession_number})"
            )

        except Exception as e:
            logger.error(
                f"Failed to download {filing_dict.get('accession_number')}: {e}",
                exc_info=True,
            )
            # Continue with next filing
            continue

    logger.info(
        f"Successfully downloaded {len(downloaded_filings)} target form filings"
    )

    return downloaded_filings


def download_8k_task(
    filing_list: List[Dict[str, Any]], **kwargs
) -> List[Dict[str, Any]]:
    """Download all Form 8-K filings.

    Args:
        filing_list: List of filing metadata dictionaries from discover task.
        **kwargs: Airflow context.

    Returns:
        List of dictionaries with filing metadata and downloaded file paths.
    """
    logger.info("Downloading all Form 8-K filings")

    # Filter for 8-K forms
    k8_filings = [
        f
        for f in filing_list
        if f.get("form_type") in ["8-K", "8K"]
    ]

    if not k8_filings:
        logger.info("No 8-K filings to download")
        return []

    output_dir = RAW_DATA_DIR / "filings"
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded_filings = []

    for filing_dict in k8_filings:
        try:
            # Convert dict back to FilingMetadata
            filing = FilingMetadata(
                cik=filing_dict["cik"],
                company_name=filing_dict["company_name"],
                form_type=filing_dict["form_type"],
                date_filed=filing_dict["date_filed"],
                file_name=filing_dict["file_name"],
                accession_number=filing_dict.get("accession_number"),
            )

            # Download filing
            downloaded_files = download_filing_with_manifest(
                filing_metadata=filing,
                output_dir=output_dir,
                download_exhibits=True,
                save_manifest=True,
            )

            downloaded_filings.append(
                {
                    "filing_metadata": filing_dict,
                    "downloaded_files": {
                        k: str(v) if isinstance(v, Path) else v
                        for k, v in downloaded_files.items()
                    },
                }
            )

            logger.info(
                f"Downloaded 8-K - {filing.company_name} "
                f"({filing.accession_number})"
            )

        except Exception as e:
            logger.error(
                f"Failed to download 8-K {filing_dict.get('accession_number')}: {e}",
                exc_info=True,
            )
            # Continue with next filing
            continue

    logger.info(
        f"Successfully downloaded {len(downloaded_filings)} 8-K filings"
    )

    return downloaded_filings


def parse_filter_8k_task(
    downloaded_8k_list: List[Dict[str, Any]], **kwargs
) -> List[Dict[str, Any]]:
    """Parse 8-K filings and filter by target items.

    Args:
        downloaded_8k_list: List of downloaded 8-K filings with file paths.
        **kwargs: Airflow context.

    Returns:
        List of filings that contain target items (1.01, 2.01, 9.01).
    """
    logger.info("Parsing and filtering 8-K filings by target items")

    if not downloaded_8k_list:
        logger.info("No 8-K filings to parse")
        return []

    parser = Form8KParser()
    filtered_filings = []

    for filing_data in downloaded_8k_list:
        filing_metadata = filing_data.get("filing_metadata", {})
        downloaded_files = filing_data.get("downloaded_files", {})
        accession_number = filing_metadata.get("accession_number")

        # Get primary HTML path
        primary_html_path = downloaded_files.get("primary_html")
        if not primary_html_path:
            logger.warning(
                f"No primary HTML found for {accession_number}, skipping"
            )
            continue

        primary_html_path = Path(primary_html_path)

        if not primary_html_path.exists():
            logger.warning(
                f"Primary HTML file not found: {primary_html_path}, skipping"
            )
            continue

        try:
            # Parse the filing
            result = parser.parse(
                filing_path=primary_html_path,
                filing_metadata=FilingMetadata(**filing_metadata),
            )

            # Check if it has target items
            # Items are stored in result["items"] dict, keys are item numbers
            items_found = list(result.get("items", {}).keys())
            has_target_items = any(
                item in items_found for item in TARGET_8K_ITEMS
            )

            if has_target_items:
                # Create filing data with parser result
                # Add items_found list to result for consistency
                parser_result = result.copy()
                parser_result["items_found"] = items_found
                
                filing_data_with_parser = {
                    "filing_metadata": filing_metadata,
                    "downloaded_files": downloaded_files,
                    "parser_result": parser_result,
                }
                filtered_filings.append(filing_data_with_parser)

                target_items_found = [
                    item for item in items_found if item in TARGET_8K_ITEMS
                ]
                logger.info(
                    f"8-K {accession_number} contains target items: "
                    f"{target_items_found}"
                )
            else:
                logger.debug(
                    f"8-K {accession_number} does not contain target items, "
                    f"skipping storage"
                )

        except Exception as e:
            logger.error(
                f"Failed to parse 8-K {accession_number}: {e}", exc_info=True
            )
            # Continue with next filing
            continue

    logger.info(
        f"Filtered {len(filtered_filings)} 8-K filings with target items "
        f"out of {len(downloaded_8k_list)} total"
    )

    return filtered_filings


def store_filings_task(
    filing_list: List[Dict[str, Any]],
    collection_name: str = None,
    **kwargs
) -> Dict[str, int]:
    """Store filings in MongoDB.

    Args:
        filing_list: List of filing dictionaries with metadata and file paths.
        collection_name: MongoDB collection name. If None, uses default.
        **kwargs: Airflow context.

    Returns:
        Dictionary with statistics:
        {
            "stored": 5,
            "skipped": 2,
            "failed": 1
        }
    """
    logger.info(f"Storing {len(filing_list)} filings in MongoDB")

    if not filing_list:
        logger.info("No filings to store")
        return {"stored": 0, "skipped": 0, "failed": 0}

    try:
        # Get MongoDB connection
        client = get_mongodb_client(MONGODB_CONNECTION_STRING)
        database = get_database(client, MONGODB_DATABASE_NAME)
        collection = get_collection(
            database, collection_name or MONGODB_COLLECTION_NAME
        )

        # Store filings
        stats = store_filings_batch(filing_list, collection)

        logger.info(
            f"MongoDB storage complete: {stats['stored']} stored, "
            f"{stats['skipped']} skipped, {stats['failed']} failed"
        )

        # Close connection
        client.close()

        return stats

    except Exception as e:
        logger.error(f"Failed to store filings in MongoDB: {e}", exc_info=True)
        raise
