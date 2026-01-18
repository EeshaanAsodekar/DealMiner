"""Form-specific configurations for parsing SEC filings."""

from typing import Dict, List

# Form 8-K relevant items for M&A
FORM_8K_MA_ITEMS: Dict[str, str] = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "9.01": "Financial Statements and Exhibits",
}

# Form S-4 relevant sections
FORM_S4_MA_SECTIONS: List[str] = [
    "merger_agreement",
    "business_combination",
    "transaction_terms",
    "financial_statements",
]

# Form 425 relevant sections
FORM_425_MA_SECTIONS: List[str] = [
    "merger_update",
    "acquisition_update",
    "transaction_update",
]

# PREM14A relevant sections
PREM14A_MA_SECTIONS: List[str] = [
    "merger_proposal",
    "shareholder_voting",
    "transaction_details",
]

# Mapping of form types to their relevant sections
FORM_SECTIONS_MAP: Dict[str, Dict] = {
    "8-K": {"type": "items", "sections": FORM_8K_MA_ITEMS},
    "S-4": {"type": "sections", "sections": FORM_S4_MA_SECTIONS},
    "425": {"type": "sections", "sections": FORM_425_MA_SECTIONS},
    "PREM14A": {"type": "sections", "sections": PREM14A_MA_SECTIONS},
    # TODO: Add configurations for other form types
}
