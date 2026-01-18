"""Brands domain constants."""

from enum import Enum

DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 50


class CompanySize(str, Enum):
    """Company size enumeration."""

    MICRO = "Micro"
    SME = "SME"
    LARGE = "Large"
