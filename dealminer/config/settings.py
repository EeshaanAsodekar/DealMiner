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

# User agent (SEC requires identifying user agent)
USER_AGENT = os.getenv("SEC_USER_AGENT", "DealMiner - M&A Data Extraction Tool contact@example.com")

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
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "dealminer" / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# MongoDB Configuration
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017/")
MONGODB_DATABASE_NAME = os.getenv("MONGODB_DATABASE_NAME", "dealminer")
MONGODB_COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME", "ma_deals")
