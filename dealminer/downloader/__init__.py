"""Downloader module for SEC filings."""

from dealminer.downloader.edgar_downloader import EdgarDownloader
from dealminer.downloader.filing_discovery import (
    FilingMetadata,
    construct_daily_index_url,
    discover_filings_for_date,
    download_daily_index,
    filter_filings_by_form_type,
    get_quarter_from_date,
    parse_daily_index,
    save_filings_to_csv,
)
from dealminer.downloader.filing_downloader import (
    download_filing_with_manifest,
    download_index_json,
    get_ma_relevant_exhibits,
    parse_index_json,
    construct_filing_base_url,
    construct_index_json_url,
)

__all__ = [
    "FilingMetadata",
    "EdgarDownloader",
    "discover_filings_for_date",
    "download_daily_index",
    "parse_daily_index",
    "filter_filings_by_form_type",
    "save_filings_to_csv",
    "construct_daily_index_url",
    "get_quarter_from_date",
    # New filing downloader functions
    "download_filing_with_manifest",
    "download_index_json",
    "parse_index_json",
    "get_ma_relevant_exhibits",
    "construct_filing_base_url",
    "construct_index_json_url",
]
