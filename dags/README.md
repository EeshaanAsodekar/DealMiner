# Airflow DAGs for DealMiner

This directory contains Apache Airflow DAGs for the DealMiner SEC filing pipeline.

## DAG: `sec_filing_pipeline`

### Description
Discover, download, and store SEC filings for M&A analysis. The DAG:
1. Discovers all target filings for a given date
2. Downloads target forms (PREM14A, SCTOT, SC14D9, S-4, 425)
3. Downloads all 8-K filings, parses them, and filters by items (1.01, 2.01, 9.01)
4. Stores all relevant filings in MongoDB

### Usage

#### Trigger with Date Parameter

When triggering the DAG from Airflow UI, provide a date in the configuration:

```json
{
  "target_date": "2025-12-22"
}
```

Or via Airflow CLI:
```bash
airflow dags trigger sec_filing_pipeline --conf '{"target_date": "2025-12-22"}'
```

If no date is provided, it defaults to yesterday's date.

#### Tasks

1. **discover_filings**: Discovers all target filings for the specified date
2. **download_target_forms**: Downloads PREM14A, SCTOT, SC14D9, S-4, 425 filings
3. **download_8k_filings**: Downloads all 8-K filings
4. **parse_filter_8k**: Parses 8-K filings and filters by target items
5. **store_filings**: Stores all relevant filings in MongoDB

### Task Dependencies

```
discover_filings
    ├──> download_target_forms ──┐
    └──> download_8k_filings ──> parse_filter_8k ──┘
                                        │
                                        └──> store_filings
```

## Setup

1. Copy `env.example` to `.env` and update MongoDB connection string
2. Start Airflow with Docker Compose:
   ```bash
   docker-compose up -d
   ```
3. Access Airflow UI at http://localhost:8080
   - Username: airflow
   - Password: airflow

## MongoDB Storage

Filings are stored in MongoDB with the following structure:
- **Connection**: Configured in `env.example` or environment variables
- **Database**: `dealminer`
- **Collection**: `rawfilings`
- **Document Structure**: See `dealminer/storage/mongodb_client.py` for details

## Notes

- The DAG is idempotent - re-running will upsert existing filings
- 8-K filings without target items (1.01, 2.01, 9.01) are not stored in MongoDB
- All downloaded files are saved locally in `dealminer/data/raw/filings/`
