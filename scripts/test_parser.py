"""Test script for parsing all 8-K SEC filings and saving to CSV."""

import csv
import logging
import re
import sys
from pathlib import Path
from typing import List

# Add parent directory to Python path so we can import dealminer
sys.path.insert(0, str(Path(__file__).parent.parent))

from dealminer.config.settings import PROCESSED_DATA_DIR
from dealminer.parser import Form8KParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def find_primary_html(filing_dir: Path) -> Path:
    """Find the primary HTML file in a filing directory.

    Args:
        filing_dir: Directory containing the filing files.

    Returns:
        Path to the primary HTML file.

    Raises:
        FileNotFoundError: If no primary HTML file is found.
    """
    # Look for HTML files
    html_files = list(filing_dir.glob("*.htm")) + list(filing_dir.glob("*.html"))

    if not html_files:
        raise FileNotFoundError(f"No HTML files found in {filing_dir}")

    # Try to identify primary HTML
    # Primary HTML files typically:
    # 1. Don't contain "R1", "CVR", "XBRL", "index" in name
    # 2. Are reasonably sized (not too small, not too large)
    # 3. May contain form type indicators (8k, d8k, etc.)

    candidates = []
    for html_file in html_files:
        name_lower = html_file.name.lower()
        size = html_file.stat().st_size

        # Skip XBRL, index, cover files
        skip_patterns = ["r1", "cvr", "xbrl", "index", "cover", "graphic"]
        if any(skip in name_lower for skip in skip_patterns):
            continue

        # Prefer files with form indicators or reasonable size
        has_form_indicator = bool(re.search(r"d\d+[a-z]?\.htm|8k\.htm", name_lower))
        reasonable_size = 10000 < size < 5000000
        if has_form_indicator or reasonable_size:
            candidates.append((html_file, size))

    if not candidates:
        # Fallback: use the largest HTML file that's not obviously wrong
        candidates = [(f, f.stat().st_size) for f in html_files if f.stat().st_size > 5000]
        candidates.sort(key=lambda x: x[1], reverse=True)

    if candidates:
        # Return the first candidate (sorted by preference)
        return candidates[0][0]

    # Last resort: return the first HTML file
    return html_files[0]


def find_exhibits(filing_dir: Path) -> List[Path]:
    """Find exhibit files in a filing directory.

    Args:
        filing_dir: Directory containing the filing files.

    Returns:
        List of paths to exhibit files.
    """
    exhibits = []
    # Look for exhibit patterns
    exhibit_patterns = ["*ex*.htm", "*ex*.html", "*EX*.htm", "*EX*.html"]
    for pattern in exhibit_patterns:
        exhibits.extend(filing_dir.glob(pattern))

    return list(set(exhibits))  # Remove duplicates


def parse_all_8k_filings(filings_dir: Path, output_csv: Path) -> None:
    """Parse all 8-K filings in a directory and save results to CSV.

    Args:
        filings_dir: Directory containing 8-K filing subdirectories.
        output_csv: Path to output CSV file.
    """
    parser = Form8KParser()

    # Get all filing directories
    filing_dirs = [d for d in filings_dir.iterdir() if d.is_dir()]

    logger.info("Found %d filing directories to parse", len(filing_dirs))

    # Prepare CSV data
    csv_rows = []
    successful_parses = 0
    failed_parses = 0

    for idx, filing_dir in enumerate(filing_dirs, 1):
        accession_number = filing_dir.name
        logger.info("[%d/%d] Parsing: %s", idx, len(filing_dirs), accession_number)

        try:
            # Find primary HTML
            primary_html = find_primary_html(filing_dir)
            logger.debug("  Primary HTML: %s", primary_html.name)

            # Find exhibits
            exhibits = find_exhibits(filing_dir)
            logger.debug("  Found %d exhibit files", len(exhibits))

            # Parse the filing
            if exhibits:
                result = parser.parse_with_exhibits(
                    filing_path=primary_html,
                    exhibit_paths=exhibits,
                    keywords=["merger", "acquisition"],
                    filing_dir=filing_dir,  # Pass filing_dir for index.json access
                )
            else:
                result = parser.parse(filing_path=primary_html)

            # Extract data for CSV
            items_found = result.get("items", {})
            relevant_exhibits = result.get("relevant_exhibits", [])

            # Item 9.01 specific exhibits
            item_901_exhibits = result.get("item_901_exhibits", [])
            item_901_ma_exhibits = result.get("item_901_ma_exhibits", [])

            # Create a row for each item found
            if items_found:
                for item_num, item_data in items_found.items():
                    # For Item 9.01, add exhibit information
                    item_901_exhibit_info = ""
                    item_901_ma_exhibit_info = ""
                    item_901_exhibit_count = 0

                    if item_num == "9.01":
                        item_901_exhibit_info = ", ".join(item_901_exhibits)
                        item_901_ma_exhibit_info = ", ".join(
                            [Path(e).name for e in item_901_ma_exhibits]
                        )
                        item_901_exhibit_count = result.get("item_901_ma_exhibit_count", 0)

                    row = {
                        "accession_number": accession_number,
                        "filing_dir": str(filing_dir),
                        "primary_html": primary_html.name,
                        "item_number": item_num,
                        "item_description": item_data.get("description", ""),
                        "item_content": item_data.get("content", ""),
                        "item_content_length": len(item_data.get("content", "")),
                        "relevant_exhibits": ", ".join(
                            [Path(e).name for e in relevant_exhibits]
                        ),  # noqa: E501
                        "relevant_exhibit_count": len(relevant_exhibits),
                        "total_exhibits": result.get("total_exhibits", 0),
                        "item_901_exhibits": item_901_exhibit_info,
                        "item_901_ma_exhibits": item_901_ma_exhibit_info,
                        "item_901_ma_exhibit_count": item_901_exhibit_count,
                    }
                    csv_rows.append(row)
            else:
                # No items found, still create a row
                row = {
                    "accession_number": accession_number,
                    "filing_dir": str(filing_dir),
                    "primary_html": primary_html.name,
                    "item_number": "",
                    "item_description": "",
                    "item_content": "",
                    "item_content_length": 0,
                    "relevant_exhibits": ", ".join(
                        [Path(e).name for e in relevant_exhibits]
                    ),  # noqa: E501
                    "relevant_exhibit_count": len(relevant_exhibits),
                    "total_exhibits": result.get("total_exhibits", 0),
                    "item_901_exhibits": "",
                    "item_901_ma_exhibits": "",
                    "item_901_ma_exhibit_count": 0,
                }
                csv_rows.append(row)

            successful_parses += 1

        except FileNotFoundError as e:
            logger.error("  Error: %s", e)
            failed_parses += 1
            # Still create a row for failed parsing
            row = {
                "accession_number": accession_number,
                "filing_dir": str(filing_dir),
                "primary_html": "",
                "item_number": "",
                "item_description": "",
                "item_content": "",
                "item_content_length": 0,
                "relevant_exhibits": "",
                "relevant_exhibit_count": 0,
                "total_exhibits": 0,
                "item_901_exhibits": "",
                "item_901_ma_exhibits": "",
                "item_901_ma_exhibit_count": 0,
            }
            csv_rows.append(row)

        except Exception as e:  # noqa: BLE001
            logger.error("  Error parsing %s: %s", accession_number, e)
            failed_parses += 1
            # Still create a row for failed parsing
            row = {
                "accession_number": accession_number,
                "filing_dir": str(filing_dir),
                "primary_html": "",
                "item_number": "",
                "item_description": "",
                "item_content": "",
                "item_content_length": 0,
                "relevant_exhibits": "",
                "relevant_exhibit_count": 0,
                "total_exhibits": 0,
                "item_901_exhibits": "",
                "item_901_ma_exhibits": "",
                "item_901_ma_exhibit_count": 0,
            }
            csv_rows.append(row)

    # Write to CSV
    logger.info("Writing %d rows to CSV: %s", len(csv_rows), output_csv)

    output_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "accession_number",
        "filing_dir",
        "primary_html",
        "item_number",
        "item_description",
        "item_content",
        "item_content_length",
        "relevant_exhibits",
        "relevant_exhibit_count",
        "total_exhibits",
        "item_901_exhibits",
        "item_901_ma_exhibits",
        "item_901_ma_exhibit_count",
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    logger.info("CSV saved to: %s", output_csv)
    logger.info("Summary: %d successful, %d failed", successful_parses, failed_parses)


if __name__ == "__main__":
    from dealminer.config.settings import RAW_DATA_DIR

    # Directory containing 8-K filings
    filings_base_dir = RAW_DATA_DIR / "filings" / "8_k"

    if not filings_base_dir.exists():
        print(f"Error: Filings directory not found: {filings_base_dir}")
        print("Please run test_download.py first to download filings.")
        exit(1)

    # Output CSV path
    output_csv_path = PROCESSED_DATA_DIR / "parsed_8k_filings.csv"

    print(f"Parsing all 8-K filings from: {filings_base_dir}")
    print(f"Output CSV: {output_csv_path}")
    print("-" * 80)

    parse_all_8k_filings(filings_base_dir, output_csv_path)

    print("\n" + "=" * 80)
    print(f"Parsing complete! Results saved to: {output_csv_path}")
