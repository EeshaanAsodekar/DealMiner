"""Airflow DAG for SEC filing discovery, download, and storage pipeline."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dags.tasks.sec_filing_tasks import (
    discover_filings_task,
    download_8k_task,
    download_target_forms_task,
    parse_filter_8k_task,
    store_filings_task,
)

from dealminer.config.settings import MONGODB_COLLECTION_NAME

# Default arguments for DAG
default_args = {
    "owner": "dealminer",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2025, 1, 1),
}

# DAG definition
dag = DAG(
    "sec_filing_pipeline",
    default_args=default_args,
    description="Discover, download, and store SEC filings for M&A analysis",
    schedule="55 4 * * *",  # 4:55 UTC = 11:55 PM EST daily
    catchup=False,
    tags=["sec", "filings", "ma"],
)


def get_target_date(**context):
    """Extract target date from DAG run configuration or logical date.

    For scheduled runs (11:55 PM daily): uses logical_date (data interval).
    For manual trigger with config: uses target_date from conf.

    Args:
        **context: Airflow context dictionary.

    Returns:
        Date string in YYYY-MM-DD format.
    """
    dag_run = context.get("dag_run")
    if dag_run and dag_run.conf and "target_date" in dag_run.conf:
        return dag_run.conf["target_date"]
    # Scheduled run: use logical_date (Airflow 2.2+)
    logical_date = context.get("logical_date") or context.get("execution_date")
    if logical_date:
        return logical_date.strftime("%Y-%m-%d")
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


# Task 1: Discover filings
discover_task = PythonOperator(
    task_id="discover_filings",
    python_callable=lambda **context: discover_filings_task(
        target_date=get_target_date(**context), **context
    ),
    dag=dag,
)

# Task 2: Download target forms (PREM14A, SCTOT, SC14D9, S-4, 425)
download_target_forms_task_op = PythonOperator(
    task_id="download_target_forms",
    python_callable=lambda **context: download_target_forms_task(
        filing_list=context["ti"].xcom_pull(
            task_ids="discover_filings", key="return_value"
        )
        or [],
        **context
    ),
    dag=dag,
)

# Task 3: Download all 8-K filings
download_8k_task_op = PythonOperator(
    task_id="download_8k_filings",
    python_callable=lambda **context: download_8k_task(
        filing_list=context["ti"].xcom_pull(
            task_ids="discover_filings", key="return_value"
        )
        or [],
        **context
    ),
    dag=dag,
)

# Task 4: Parse and filter 8-K filings by target items
parse_filter_8k_task_op = PythonOperator(
    task_id="parse_filter_8k",
    python_callable=lambda **context: parse_filter_8k_task(
        downloaded_8k_list=context["ti"].xcom_pull(
            task_ids="download_8k_filings", key="return_value"
        )
        or [],
        **context
    ),
    dag=dag,
)


def combine_and_store(**context):
    """Combine target forms and filtered 8-K filings, then store.

    Args:
        **context: Airflow context dictionary.

    Returns:
        Storage statistics dictionary.
    """
    # Get target forms
    target_forms = (
        context["ti"]
        .xcom_pull(task_ids="download_target_forms", key="return_value") or []
    )

    # Get filtered 8-K filings
    filtered_8k = (
        context["ti"].xcom_pull(task_ids="parse_filter_8k", key="return_value")
        or []
    )

    # Combine all filings
    all_filings = target_forms + filtered_8k

    # Store in MongoDB
    return store_filings_task(
        filing_list=all_filings,
        collection_name=MONGODB_COLLECTION_NAME,
        **context
    )


# Task 5: Store all filings in MongoDB
store_task = PythonOperator(
    task_id="store_filings",
    python_callable=combine_and_store,
    dag=dag,
)

# Define task dependencies
discover_task >> [download_target_forms_task_op, download_8k_task_op]
download_8k_task_op >> parse_filter_8k_task_op
[download_target_forms_task_op, parse_filter_8k_task_op] >> store_task
