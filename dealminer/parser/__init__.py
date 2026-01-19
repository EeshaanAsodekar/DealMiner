"""Parser module for SEC filings."""

from dealminer.parser.base_parser import BaseParser
from dealminer.parser.form8k_parser import Form8KParser
from dealminer.parser.parser_factory import get_parser, parse_filing

__all__ = [
    "BaseParser",
    "Form8KParser",
    "get_parser",
    "parse_filing",
]
