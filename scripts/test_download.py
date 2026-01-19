"""Test script for downloading SEC filings."""

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
    from datetime import date
    from dealminer.config.settings import RAW_DATA_DIR

    # Test with a recent date - discover filings first
    test_date = date(2025, 12, 22)
    print(f"Discovering filings for {test_date}...")

    try:
        # Discover filings
        filings, csv_path = discover_filings_for_date(
            filing_date=test_date,
            save_index_file=False,  # We already have this
        )

        print(f"\nFound {len(filings)} filings")

        if not filings:
            print("No filings to download.")
            exit(0)

        # Download all filings
        output_dir = RAW_DATA_DIR / "filings"

        print(f"\nDownloading {len(filings)} filings to {output_dir}...")
        print("-" * 80)

        successful_downloads = 0
        failed_downloads = 0

        for idx, filing in enumerate(filings, 1):
            print(
                f"\n[{idx}/{len(filings)}] Downloading: {filing.form_type} - {filing.company_name}"
            )
            print(f"  CIK: {filing.cik}")
            print(f"  Accession: {filing.accession_number}")

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
                    print(f"  ✓ Primary HTML: {downloaded_files['primary_html'].name}")
                if "exhibits" in downloaded_files and downloaded_files["exhibits"]:
                    print(
                        f"  ✓ Exhibits ({len(downloaded_files['exhibits'])}): {', '.join(downloaded_files['exhibits'].keys())}"
                    )

            except Exception as e:
                failed_downloads += 1
                print(f"  ✗ Failed to download: {e}")

        print("\n" + "=" * 80)
        print(f"Download Summary:")
        print(f"  Total filings: {len(filings)}")
        print(f"  Successful: {successful_downloads}")
        print(f"  Failed: {failed_downloads}")
        print(f"  Output directory: {output_dir}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("The daily index may not exist for this date (weekend/holiday).")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
