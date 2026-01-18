# DealMiner - Architecture and Design Document

## Overview

DealMiner is a modular data pipeline designed to extract M&A deal information from SEC filings. The system is built with Apache Airflow in mind, making each component easily orchestratable as a DAG task.

## Core Design Principles

1. **Modularity**: Each component is independent and can be tested/run separately
2. **Airflow-Ready**: Functions are pure and return values, making them ideal for Airflow tasks
3. **Extensibility**: Easy to add new form types and extractors
4. **Clean Code**: Simple, readable Python code following best practices
5. **Configuration-Driven**: Settings externalized to config files

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Apache Airflow DAG                        │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Discover │───▶│ Download │───▶│  Extract │───▶│   Store  │  │
│  │  Filings  │    │  Filings │    │    M&A   │    │   MongoDB │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Folder Structure

```
DealMiner/
│
├── dealminer/                          # Main package directory
│   ├── __init__.py
│   │
│   ├── config/                         # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py                 # App settings and constants
│   │   └── form_configs.py             # Form-specific configurations
│   │
│   ├── data/                           # Data directory (gitignored)
│   │   ├── raw/                        # Raw downloaded filings
│   │   │   ├── 8-k/
│   │   │   ├── s-4/
│   │   │   └── ...
│   │   └── processed/                  # Processed/parsed filings
│   │
│   ├── downloader/                     # Download module
│   │   ├── __init__.py
│   │   ├── base_downloader.py          # Abstract base downloader
│   │   ├── edgar_downloader.py         # SEC EDGAR downloader
│   │   └── filing_discovery.py         # Discover relevant filings
│   │
│   ├── parser/                         # Parsing module
│   │   ├── __init__.py
│   │   ├── base_parser.py              # Abstract base parser
│   │   ├── form8k_parser.py            # Form 8-K parser
│   │   ├── forms4_parser.py            # Form S-4 parser
│   │   ├── form425_parser.py           # Form 425 parser
│   │   ├── prem14a_parser.py           # PREM14A parser
│   │   └── parser_factory.py           # Factory to get right parser
│   │
│   ├── extractor/                      # Extraction module
│   │   ├── __init__.py
│   │   ├── base_extractor.py           # Abstract base extractor
│   │   ├── ma_extractor.py             # M&A-specific extractor
│   │   └── data_models.py              # Pydantic models for extracted data
│   │
│   ├── storage/                        # Storage module
│   │   ├── __init__.py
│   │   ├── mongodb_client.py           # MongoDB connection and operations
│   │   └── models.py                   # MongoDB document schemas
│   │
│   └── utils/                          # Utility functions
│       ├── __init__.py
│       ├── text_processing.py          # Text cleaning, normalization
│       ├── date_utils.py               # Date parsing and formatting
│       └── validation.py               # Data validation helpers
│
├── dags/                               # Airflow DAGs directory
│   ├── __init__.py
│   └── ma_pipeline_dag.py              # Main M&A extraction DAG
│
├── tests/                              # Test suite
│   ├── __init__.py
│   ├── test_downloader/
│   ├── test_parser/
│   ├── test_extractor/
│   └── test_storage/
│
├── scripts/                            # Standalone utility scripts
│   ├── test_download.py                # Test downloading functionality
│   └── test_parser.py                  # Test parsing functionality
│
├── .env.example                        # Example environment variables
├── .gitignore
├── requirements.txt                    # Python dependencies
├── setup.py                            # Package setup (if needed)
├── README.md
├── project_description.md
└── ARCHITECTURE.md                     # This file
```

## Module Breakdown

### 1. Configuration (`dealminer/config/`)

**Purpose**: Centralized configuration management

- `settings.py`: Application-wide settings (SEC URLs, rate limits, etc.)
- `form_configs.py`: Form-specific configurations (relevant items, sections, etc.)

**Key Design**:
- Use Python dataclasses or Pydantic for type safety
- Load from environment variables and config files
- Easy to override in Airflow connections/variables

### 2. Downloader Module (`dealminer/downloader/`)

**Purpose**: Download SEC filings from EDGAR

**Components**:
- `base_downloader.py`: Abstract base class for all downloaders
- `edgar_downloader.py`: SEC EDGAR-specific implementation
  - Methods: `download_filing()`, `get_filing_content()`
- `filing_discovery.py`: Discover relevant filings by form type and date range
  - Methods: `discover_filings()`, `filter_ma_relevant()`

**Key Functions for Airflow**:
```python
def discover_filings(form_types: List[str], start_date: date, end_date: date) -> List[FilingMetadata]
def download_filing(filing_metadata: FilingMetadata, output_dir: Path) -> Path
```

### 3. Parser Module (`dealminer/parser/`)

**Purpose**: Parse raw filing HTML/XML/text into structured sections

**Components**:
- `base_parser.py`: Abstract base class with interface `parse()`
- Form-specific parsers (e.g., `form8k_parser.py`):
  - Extract relevant sections (Item 1.01, 2.01, etc.)
  - Handle variations in formatting
- `parser_factory.py`: Returns appropriate parser based on form type

**Key Functions for Airflow**:
```python
def parse_filing(filing_path: Path, form_type: str) -> ParsedFiling
```

**Design Pattern**: Strategy pattern - each form type has its own parser

### 4. Extractor Module (`dealminer/extractor/`)

**Purpose**: Extract M&A-specific data points from parsed filings

**Components**:
- `base_extractor.py`: Abstract base extractor
- `ma_extractor.py`: M&A-specific extraction logic
  - Extract: company names, transaction values, dates, deal terms
- `data_models.py`: Pydantic models for extracted data
  - `MAExtractedData`: Structured output with validation

**Key Functions for Airflow**:
```python
def extract_ma_data(parsed_filing: ParsedFiling) -> Optional[MAExtractedData]
```

### 5. Storage Module (`dealminer/storage/`)

**Purpose**: Store extracted data in MongoDB

**Components**:
- `mongodb_client.py`: MongoDB connection and CRUD operations
  - Methods: `save_extracted_data()`, `upsert_deal()`
- `models.py`: MongoDB document schemas (using Pydantic or plain dicts)

**Key Functions for Airflow**:
```python
def save_ma_record(ma_data: MAExtractedData, connection_string: str) -> str  # Returns document ID
```

### 6. Utilities (`dealminer/utils/`)

**Purpose**: Reusable helper functions

- `text_processing.py`: Clean text, normalize whitespace, remove noise
- `date_utils.py`: Parse various date formats from filings
- `validation.py`: Validate extracted data before storage

## Data Flow

1. **Discovery** → Returns list of `FilingMetadata` objects
2. **Download** → Downloads filing, saves to `data/raw/{form_type}/`, returns `Path`
3. **Parse** → Reads file, extracts relevant sections, returns `ParsedFiling`
4. **Extract** → Extracts M&A fields, returns `MAExtractedData` or `None` if not M&A-related
5. **Store** → Saves to MongoDB, returns document ID

## Data Models

### FilingMetadata (dataclass)
```python
@dataclass
class FilingMetadata:
    form_type: str
    company_name: str
    cik: str
    filing_date: date
    url: str
    accession_number: str
```

### ParsedFiling (dataclass)
```python
@dataclass
class ParsedFiling:
    filing_metadata: FilingMetadata
    form_type: str
    sections: Dict[str, str]  # e.g., {"1.01": "content...", "2.01": "content..."}
    raw_text: str
```

### MAExtractedData (Pydantic Model)
```python
class MAExtractedData(BaseModel):
    filing_type: str
    filing_date: date
    company_name: Optional[str]
    target_company_name: Optional[str]
    transaction_value: Optional[Decimal]
    transaction_date: Optional[date]
    form_url: str
    extracted_text: str
    additional_details: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
```

## Airflow Integration Strategy

### DAG Structure

```python
from dealminer.downloader import discover_filings, download_filing
from dealminer.parser import parse_filing
from dealminer.extractor import extract_ma_data
from dealminer.storage import save_ma_record

def ma_pipeline_dag():
    discover_task = PythonOperator(
        task_id='discover_filings',
        python_callable=discover_filings,
        op_kwargs={'form_types': ['8-K', 'S-4'], 'start_date': '...', 'end_date': '...'}
    )
    
    download_task = PythonOperator(
        task_id='download_filings',
        python_callable=download_filing,
        # Uses XCom to get filing metadata from discover_task
    )
    
    # ... etc
```

### Key Design Decisions for Airflow:

1. **Pure Functions**: Each function takes inputs and returns outputs (no side effects in business logic)
2. **XCom Compatibility**: Return values are JSON-serializable (use dataclasses or Pydantic)
3. **Idempotency**: Re-running tasks should be safe (check if filing already downloaded/processed)
4. **Error Handling**: Functions raise exceptions that Airflow can catch and retry
5. **Task Granularity**: Each major step (discover, download, parse, extract, store) is a separate task

## Error Handling Strategy

1. **Download Failures**: Retry with exponential backoff (Airflow retry logic)
2. **Parse Failures**: Log error, skip filing, continue with next
3. **Extraction Failures**: If no M&A data found, return `None` (not an error)
4. **Storage Failures**: Retry logic at Airflow level

## Testing Strategy

- **Unit Tests**: Each module tested independently with mock data
- **Integration Tests**: Test full pipeline with sample filings
- **Fixtures**: Sample SEC filings in `tests/fixtures/`

## Configuration Management

- Use `.env` files for local development
- Use Airflow Variables/Connections for production
- Config hierarchy: Environment variables > Config file > Defaults

## Future Extensibility

- **New Form Types**: Add new parser class, register in factory
- **New Extraction Fields**: Extend `MAExtractedData` model
- **New Data Sources**: Implement new downloader class
- **Alternative Storage**: Abstract storage interface, add new implementations

## Dependencies

Key Python packages:
- `requests`: HTTP requests to SEC
- `beautifulsoup4`: HTML/XML parsing
- `lxml`: Fast XML parsing
- `pymongo`: MongoDB driver
- `pydantic`: Data validation and models
- `python-dotenv`: Environment variable management
- `apache-airflow`: DAG orchestration
