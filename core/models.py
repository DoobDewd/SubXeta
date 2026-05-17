"""Data models for subtitle generation."""
from dataclasses import dataclass


@dataclass
class Word:
    """Single word with timing information."""
    text: str
    start: float
    end: float


@dataclass
class TextVariant:
    """English and alien text pair."""
    english: str
    alien: str
