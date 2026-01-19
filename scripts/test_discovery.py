"""Test script for filing discovery functionality."""

import logging
import sys
from datetime import date
from pathlib import Path

# Add parent directory to Python path so we can import dealminer
sys.path.insert(0, str(Path(__file__).parent.parent))

from dealminer.downloader import discover_filings_for_date

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    # Test with a recent date
    test_date = date(2025, 12, 22)  # Change this to a recent date

    print(f"Discovering filings for {test_date}...")

    try:
        filings, csv_path = discover_filings_for_date(
            filing_date=test_date,
            save_index_file=True,  # Save the raw index file
        )

        print(f"\nFound {len(filings)} filings matching target form types")
        print(f"Results saved to: {csv_path}")

        # Print first few filings as sample
        if filings:
            print("\nSample filings:")
            for filing in filings[:5]:
                print(f"  {filing.form_type} - {filing.company_name} (CIK: {filing.cik})")
        else:
            print("No filings found for the specified date and form types.")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("The daily index may not exist for this date (weekend/holiday).")
    except Exception as e:
        print(f"Error: {e}")
