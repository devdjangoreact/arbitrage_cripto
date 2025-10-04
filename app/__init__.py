"""
Arbitrage Crypto Analysis Application

This package contains the core analysis modules for cryptocurrency arbitrage detection.
"""

from .arbitrage_analyzer import AnalyzeArbitrage
from .token_analyzer import TokensAnalyzer

__version__ = "1.0.0"
__author__ = "Arbitrage Crypto Team"

__all__ = [
    "AnalyzeArbitrage",
    "TokensAnalyzer",
]
