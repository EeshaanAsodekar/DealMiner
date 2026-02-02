"""Application-wide settings and constants."""

import os
from pathlib import Path
from typing import List

# SEC EDGAR Configuration
SEC_EDGAR_BASE_URL = "https://www.sec.gov"
SEC_EDGAR_SEARCH_URL = f"{SEC_EDGAR_BASE_URL}/cgi-bin/browse-edgar"
SEC_EDGAR_API_URL = f"{SEC_EDGAR_BASE_URL}/cgi-bin"

# Rate limiting (SEC requires delays between requests)
REQUEST_DELAY_SECONDS = float(os.getenv("SEC_REQUEST_DELAY", "0.1"))

# User agent (SEC requires identifying user agent – set SEC_USER_AGENT in .env)
USER_AGENT = os.getenv("SEC_USER_AGENT", "DealMiner/0.1 (set SEC_USER_AGENT in .env)")

# Supported SEC Form Types for M&A
SUPPORTED_FORM_TYPES: List[str] = [
    "8-K",
    "PREM14A",
    "SCTOT",
    "SC14D9",
    "S-4",
    "13D",
    "425",
]

# SEC Daily Index URL template
SEC_DAILY_INDEX_BASE_URL = f"{SEC_EDGAR_BASE_URL}/Archives/edgar/daily-index"

# Data directories
# When running in Airflow Docker, use /opt/airflow/data (mounted rw) instead of dealminer/data (ro)
BASE_DIR = Path(__file__).parent.parent.parent
_DATA_DIR_ENV = os.getenv("DEALMINER_DATA_DIR")
if _DATA_DIR_ENV:
    DATA_DIR = Path(_DATA_DIR_ENV)
else:
    DATA_DIR = BASE_DIR / "dealminer" / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# MongoDB Configuration (all from .env / environment – no defaults for secrets)
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
MONGODB_DATABASE_NAME = (
    os.getenv("MONGODB_DATABASE_NAME") or os.getenv("MONGODB_DATABASE", "dealminer")
)
MONGODB_COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME", "rawfilings")
