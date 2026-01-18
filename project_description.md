# DealMiner

# Developer Documentation for Mergers and Acquisitions (M&A) Dataset Extraction from SEC Filings

## Table of Contents

1. [Overview]
2. [Objectives]
3. [Data Sources]
4. [System Architecture]
5. [Data Retrieval]
6. [Data Parsing and Extraction]
    - [Handling Different SEC Forms]
    - [Parsing Form 8-K]
7. [Data Storage]
8. [Tools and Libraries]
9. [Existing Solutions]
10. [Resources and References]
11. [Examples]
12. [Additional Considerations]

---

## Overview

This documentation outlines the development of a system designed to parse and extract mergers and acquisitions (M&A) data from various Securities and Exchange Commission (SEC) filings. The goal is to compile a comprehensive M&A dataset by processing multiple types of SEC documents that signal merger-related activities.

## Objectives

- **Data Collection:** Download relevant SEC filings that may contain M&A information.
- **Data Parsing:** Extract pertinent M&A data from the filings.
- **Data Structuring:** Organize extracted data into a structured dataset.
- **Data Storage:** Store the structured data in a database for easy access and analysis.
- **Automation:** Develop an automated pipeline to continuously update the dataset with new filings.

## Data Sources

Several SEC filings can indicate merger-related activities. The primary forms to target include:

- **Form 8-K:** Reports important events or material information, including mergers and acquisitions.
- **PREM14A:** Preliminary proxy statements.
- **SCTOT:** Tender offer documents.
- **SC14D9:** Schedule 14D-9 for tender offers.
- **Form S-4:** Registration statement for business combinations.
- **Form 13D:** Filed by individuals or groups owning 5% or more of a company’s stock.
- **Form 4:** Filed by insiders buying or selling company stock.
- **Form 425:** Disclosures related to mergers, acquisitions, and other business combinations.

### Additional Resources

- **Mergershark Trial:** [Sign Up for Free Trial](https://mergershark.com/users/sign_up)
- **WallStreetPrep on M&A Transactions:** [Deal Documents for M&A](https://www.wallstreetprep.com/knowledge/deal-documents-go-find-information-ma-transactions/)
- **GitHub Repositories:**
    - [Explainable Financial Text Classification](https://github.com/YangLinyi/Explainable-Financial-Text-Classification)
    - [Mergers and Acquisitions Stock Price Prediction](https://github.com/Wiqzard/Mergers-and-Acquisitions-Stock-Price-Prediction)
- **Kaggle Dataset:** [Company Acquisitions Dataset](https://www.kaggle.com/datasets/shivamb/company-acquisitions-7-top-companies)

## System Architecture

The system comprises the following components:

1. **Data Ingestion Module:** Downloads SEC filings from sources like EDGAR or third-party providers.
2. **Data Parsing Module:** Parses downloaded filings to extract relevant M&A information.
3. **Data Extraction Module:** Identifies and extracts specific data points related to mergers and acquisitions.
4. **Data Storage Module:** Stores the extracted data in a structured format (e.g., SQL/NoSQL databases).
5. **Automation Scheduler:** Automates the periodic downloading and processing of new filings.
6. **User Interface (Optional):** Provides access to the dataset for analysis and visualization.

![](https://i.imgur.com/YourDiagramLink.png)

*(Replace with actual diagram if available)*

## Data Retrieval

### Accessing SEC Filings

1. **EDGAR Database:** The primary source for SEC filings.
    - **API Access:** Utilize the EDGAR API for automated retrieval.
    - **Web Scraping:** If API access is limited, employ web scraping techniques.
2. **Third-Party Providers:** Services like [Mergershark](https://mergershark.com/users/sign_up) offer enriched datasets and APIs.

### Steps to Retrieve Filings

1. **Identify Relevant Filings:**
    - Use advanced search features to filter filings by form type (e.g., "Form 8-K", "Form S-4").
    - Keywords: "Agreement and Plan of Merger", target/acquirer names.
2. **Download Filings:**
    - Automate downloads using scripts that interact with the EDGAR API or scrape the SEC website.
    - Ensure compliance with SEC's [Terms of Use](https://www.sec.gov/privacy.htm).

## Data Parsing and Extraction

### Handling Different SEC Forms

Each SEC form has a unique structure and contains different sections relevant to M&A activities.

### Form 8-K

- **Purpose:** Reports major events, including M&A activities.
- **Key Items for M&A:**
    - **Item 1.01:** Entry into a Material Definitive Agreement
    - **Item 2.01:** Completion of Acquisition or Disposition of Assets
    - **Item 9.01:** Financial Statements and Exhibits

### PREM14A

- **Purpose:** Preliminary proxy statements related to mergers.
- **Key Sections:** Merger proxies and shareholder voting information.

### SCTOT & SC14D9

- **Purpose:** Tender offer documents.
- **Key Sections:** Details of the tender offer, terms, and conditions.

### Form S-4

- **Purpose:** Registration for business combinations.
- **Key Sections:** Merger agreement details, financial statements, and terms.

### Form 13D & Form 4

- **Purpose:** Disclosure of significant stock ownership and insider transactions.
- **Key Sections:** Ownership changes that may indicate strategic moves towards M&A.

### Form 425

- **Purpose:** Updates on mergers, acquisitions, and business combinations.
- **Key Sections:** Changes to previously filed information related to M&A.

### Parsing Logic

1. **Load Filing Content:**
    - Use parsers like BeautifulSoup for HTML/XML content or plain text processing.
2. **Identify Relevant Sections:**
    - Locate specific items (e.g., Item 1.01, Item 2.01) within the filings.
    - Utilize regular expressions or XML tags to find sections.
3. **Extract Information:**
    - Retrieve text related to deal announcements, financial terms, parties involved, etc.
    - Example Code Snippet for Form 8-K:
    
    ```python
    from bs4 import BeautifulSoup
    
    def extract_deal_announcement(file_content):
        soup = BeautifulSoup(file_content, 'html.parser')
        item1 = soup.find(['item1', 'item 1.'])  # Handles variations
        item7 = soup.find(['item7', 'item 7.'])
        if item1 and item7:
            deal_announcement = item1.get_text(separator='\\n') + '\\n' + item7.get_text(separator='\\n')
            return deal_announcement
        return None
    
    ```
    
4. **Normalize Data:**
    - Standardize extracted information (e.g., dates, monetary values).
    - Handle variations in terminology and formatting.

### Example: Parsing Form 8-K

Form 8-K filings contain multiple items, each representing different events. For M&A-related data, focus on specific items.

### List of Relevant Items with Examples

1. **Item 1.01 - Entry into a Material Definitive Agreement**
    - **Example:** "On March 1, 2023, XYZ Corporation entered into a definitive agreement to acquire 100% of ABC Corporation for $10 billion in cash."
2. **Item 1.02 - Termination of a Material Definitive Agreement**
    - **Example:** "XYZ Corporation terminated its merger agreement with ABC Corporation due to regulatory issues."
3. **Item 2.01 - Completion of Acquisition or Disposition of Assets**
    - **Example:** "XYZ Corporation completed its acquisition of ABC Corporation for $10 billion in cash."
4. **Item 9.01 - Financial Statements and Exhibits**
    - **Example:** "The financial statements reflect the impact of the recent acquisition of ABC Corporation."

### Comprehensive Example

```python
def parse_form_8k(file_content):
    soup = BeautifulSoup(file_content, 'html.parser')
    sections = {}
    relevant_items = {
        '1.01': 'Entry into a Material Definitive Agreement',
        '1.02': 'Termination of a Material Definitive Agreement',
        '2.01': 'Completion of Acquisition or Disposition of Assets',
        '9.01': 'Financial Statements and Exhibits'
    }

    for item, description in relevant_items.items():
        tag = soup.find(['item' + item.replace('.', ''), 'item ' + item.replace('.', '')])
        if tag:
            sections[item] = {
                'description': description,
                'content': tag.get_text(separator='\\n').strip()
            }

    return sections

```

## Data Storage

### Database Selection

- **Relational Databases (e.g., PostgreSQL, MySQL):** Suitable for structured data with relationships.
- **NoSQL Databases (e.g., MongoDB):** Ideal for handling unstructured or semi-structured data.

### Suggested Schema

**MergersAndAcquisitions Table:**

| Column Name | Data Type | Description |
| --- | --- | --- |
| id | UUID | Unique identifier for each M&A record |
| filing_type | VARCHAR | Type of SEC filing (e.g., 8-K, S-4) |
| filing_date | DATE | Date of the SEC filing |
| company_name | VARCHAR | Name of the acquiring company |
| target_company_name | VARCHAR | Name of the target company |
| transaction_value | DECIMAL | Monetary value of the transaction |
| transaction_date | DATE | Date when the transaction was announced/completed |
| form_url | TEXT | URL to the original SEC filing |
| extracted_text | TEXT | Raw extracted text related to the transaction |
| additional_details | JSONB | Any other relevant details (e.g., financing terms) |
| created_at | TIMESTAMP | Timestamp when the record was created |
| updated_at | TIMESTAMP | Timestamp when the record was last updated |

### Data Ingestion

- **Batch Processing:** Periodically run scripts to download and process new filings.
- **Real-Time Processing (Optional):** Implement event-driven architectures to handle filings as they are released.

## Tools and Libraries

- **Programming Language:** Python
- **Web Scraping:** BeautifulSoup, Requests
- **XML Parsing:** lxml, BeautifulSoup
- **PDF Parsing (if needed):** pdfminer.six, PyPDF2
- **Natural Language Processing:** NLTK, spaCy, regex
- **Data Storage:** SQLAlchemy (for ORM), pymongo (for MongoDB)
- **Automation:** Cron jobs, Airflow
- **Version Control:** GitHub

### Example Python Libraries

```python
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import sqlalchemy
# Add other necessary imports

```

## Existing Solutions

Before developing the system, it's prudent to explore existing solutions to avoid redundancy and leverage existing tools.

### GitHub Repositories

- [**Explainable Financial Text Classification](https://github.com/YangLinyi/Explainable-Financial-Text-Classification):** Tools for classifying financial texts, which can aid in identifying M&A-related sections.
- [**Mergers and Acquisitions Stock Price Prediction](https://github.com/Wiqzard/Mergers-and-Acquisitions-Stock-Price-Prediction):** Models predicting stock price movements post-M&A.

### Kaggle Datasets

- [**Company Acquisitions Dataset](https://www.kaggle.com/datasets/shivamb/company-acquisitions-7-top-companies):** Precompiled data on company acquisitions, which can be used for benchmarking.

### Recommendations

- **Leverage Existing Code:** Utilize parsers and classifiers from existing repositories to expedite development.
- **Contribute Back:** If enhancements are made, consider contributing to open-source projects to benefit the community.

## Resources and References

- **SEC EDGAR Filings:** [SEC EDGAR Database](https://www.sec.gov/edgar.shtml)
- **SEC Forms Guide:** [SEC Forms and Filing Tips](https://www.sec.gov/forms)
- **Mergershark:** [Mergershark Trial](https://mergershark.com/users/sign_up)
- **WallStreetPrep on M&A:** [Deal Documents for M&A](https://www.wallstreetprep.com/knowledge/deal-documents-go-find-information-ma-transactions/)
- **Reddit Discussion on Form 8-K Amendments:** [Reddit Link](https://www.reddit.com/r/BBBY/comments/10zdrg1/omgwhy_no_one_mentions_this_todays_amendment_8k/)
- **Studies on M&A Deal Leaks:**
    - **Intralinks Holdings Inc. (2015):** Analyzed 3,500 global M&A deals, finding 10.3% had leaked before official announcements.
    - **Columbia Business School and Rutgers Business School (2018):** Analyzed 1,713 M&A deals, finding 23% had leaks prior to official announcements.

## Examples

### Parsing Form 8-K Filing

Given a sample Form 8-K filing, the system should extract M&A-related information from relevant items.

### Sample Filing Content

```html
<Item 1.01 Entry into a Material Definitive Agreement>

On March 1, 2023, XYZ Corporation (“XYZ”) entered into a definitive agreement to acquire 100% of the outstanding shares of ABC Corporation (“ABC”) for $10 billion in cash. The transaction is subject to customary closing conditions, including regulatory approvals, and is expected to close in the second quarter of 2023.

<Item 2.01 Completion of Acquisition or Disposition of Assets>

On March 5, 2023, XYZ Corporation (“XYZ”) completed its acquisition of 100% of the outstanding shares of ABC Corporation (“ABC”) for $10 billion in cash. As a result of the acquisition, ABC is now a wholly owned subsidiary of XYZ. The transaction was funded through a combination of cash on hand and debt financing.

```

### Parsing Outcome

```json
{
  "1.01": {
    "description": "Entry into a Material Definitive Agreement",
    "content": "On March 1, 2023, XYZ Corporation (“XYZ”) entered into a definitive agreement to acquire 100% of the outstanding shares of ABC Corporation (“ABC”) for $10 billion in cash. The transaction is subject to customary closing conditions, including regulatory approvals, and is expected to close in the second quarter of 2023."
  },
  "2.01": {
    "description": "Completion of Acquisition or Disposition of Assets",
    "content": "On March 5, 2023, XYZ Corporation (“XYZ”) completed its acquisition of 100% of the outstanding shares of ABC Corporation (“ABC”) for $10 billion in cash. As a result of the acquisition, ABC is now a wholly owned subsidiary of XYZ. The transaction was funded through a combination of cash on hand and debt financing."
  }
}

```

### Extracted M&A Data Record

| id | filing_type | filing_date | company_name | target_company_name | transaction_value | transaction_date | form_url | extracted_text | additional_details | created_at | updated_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8-K | 2023-03-01 | XYZ Corp | ABC Corp | 10,000,000,000 | 2023-03-05 | [Link] | *Full extracted text* | {"financing": "cash on hand and debt financing"} | 2024-04-27 | 2024-04-27 |

## Additional Considerations

### Data Quality and Validation

- **Consistency Checks:** Ensure that extracted data aligns across different filings (e.g., transaction value matches across Form 8-K and Form S-4).
- **Error Handling:** Implement robust error handling for missing sections, malformed filings, or unexpected formats.
- **Data Enrichment:** Cross-reference with other data sources (e.g., company databases) to enhance data quality.

### Scalability

- **Handling Volume:** Optimize the system to handle large volumes of filings, especially during peak M&A activity periods.
- **Performance Optimization:** Utilize asynchronous processing, caching, and efficient parsing techniques.

### Security and Compliance

- **Data Privacy:** Ensure compliance with data privacy laws and SEC regulations.
- **Secure Storage:** Protect sensitive data through encryption and secure access controls.

### Maintenance and Updates

- **Regular Updates:** Keep the system updated with changes in SEC filing formats or new types of filings.
- **Monitoring:** Implement monitoring to track system performance and detect issues promptly.

### Future Enhancements

- **Natural Language Processing (NLP):** Utilize NLP techniques to improve the accuracy of data extraction.
- **Machine Learning Models:** Develop models to predict M&A activities based on extracted data.
- **User Interface:** Build dashboards and visualization tools for data analysis.

---

By following this documentation, developers can create a robust system to extract, process, and store M&A data from various SEC filings, thereby enabling comprehensive analysis and insights into merger and acquisition activities