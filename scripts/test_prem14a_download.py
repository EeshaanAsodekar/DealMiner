"""Test script for downloading PREM14A filings."""

import logging
import sys
from pathlib import Path

# Add parent directory to Python path so we can import dealminer
sys.path.insert(0, str(Path(__file__).parent.parent))

from dealminer.downloader import (
    discover_filings_for_date,
    download_filing_with_manifest,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    from datetime import date, timedelta

    from dealminer.config.settings import RAW_DATA_DIR

    # Download PREM14A filings for entire month of December 2025
    start_date = date(2025, 12, 1)
    end_date = date(2025, 12, 31)

    print(f"Discovering PREM14A filings from {start_date} to {end_date}...")
    print("=" * 80)

    all_filings = []
    current_date = start_date

    # Discover filings for each day in December
    while current_date <= end_date:
        print(f"\nProcessing date: {current_date}...")

        try:
            # Discover PREM14A filings for this date
            filings, csv_path = discover_filings_for_date(
                filing_date=current_date,
                form_types=["PREM14A"],  # Only PREM14A
                save_index_file=False,
            )

            print(f"  Found {len(filings)} PREM14A filings for {current_date}")
            all_filings.extend(filings)

        except FileNotFoundError:
            # Daily index doesn't exist (weekend/holiday) - skip
            print(f"  No index file for {current_date} (weekend/holiday) - skipping")
        except Exception as e:
            print(f"  Error discovering filings for {current_date}: {e}")

        # Move to next day
        current_date += timedelta(days=1)

    print("\n" + "=" * 80)
    print(f"Total PREM14A filings found across all dates: {len(all_filings)}")

    if not all_filings:
        print("No PREM14A filings to download.")
        exit(0)

    # Download all PREM14A filings
    output_dir = RAW_DATA_DIR / "filings"

    print(f"\nDownloading {len(all_filings)} PREM14A filings to {output_dir}...")
    print("-" * 80)

    successful_downloads = 0
    failed_downloads = 0

    for idx, filing in enumerate(all_filings, 1):
        print(
            f"\n[{idx}/{len(all_filings)}] Downloading: {filing.form_type} - {filing.company_name}"
        )
        print(f"  CIK: {filing.cik}")
        print(f"  Accession: {filing.accession_number}")
        print(f"  Date Filed: {filing.date_filed}")

        try:
            downloaded_files = download_filing_with_manifest(
                filing_metadata=filing,
                output_dir=output_dir,
                download_exhibits=True,
                save_manifest=True,
            )

            successful_downloads += 1

            # Show what was downloaded
            if "primary_html" in downloaded_files:
                print(
                    f"  ✓ Primary HTML: {downloaded_files['primary_html'].name}"
                )
            if "exhibits" in downloaded_files and downloaded_files["exhibits"]:
                exhibit_types = ", ".join(downloaded_files["exhibits"].keys())
                print(
                    f"  ✓ Exhibits ({len(downloaded_files['exhibits'])}): {exhibit_types}"
                )

        except Exception as e:
            failed_downloads += 1
            print(f"  ✗ Failed to download: {e}")

    print("\n" + "=" * 80)
    print("Download Summary:")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Total filings discovered: {len(all_filings)}")
    print(f"  Successful downloads: {successful_downloads}")
    print(f"  Failed downloads: {failed_downloads}")
    print(f"  Output directory: {output_dir}")
