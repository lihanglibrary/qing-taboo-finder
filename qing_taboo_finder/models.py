"""Core data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class EmperorRecord:
    sequence: int
    emperor: str
    name: str
    traditional_name: str
    taboo_traditional: list[str] = field(default_factory=list)
    taboo_simplified: list[str] = field(default_factory=list)
    taboo_radical: list[str] = field(default_factory=list)
    taboo_substitute: list[str] = field(default_factory=list)
    proper_noun_simplified: list[str] = field(default_factory=list)
    proper_noun_traditional: list[str] = field(default_factory=list)
    original_proper_noun_simplified: list[str] = field(default_factory=list)
    original_proper_noun_traditional: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TabooEntry:
    token: str
    category: str
    emperor: str
    source_sequence: int
    is_current_reign: bool


@dataclass(slots=True)
class LoadedDocument:
    path: Path
    text: str
    title: str


@dataclass(slots=True)
class TextSegment:
    index: int
    title: str
    text: str
    start_offset: int


@dataclass(slots=True)
class DetectionHit:
    document_name: str
    segment_index: int
    segment_title: str
    matched_text: str
    category: str
    emperor: str
    emperor_sequence: int
    is_cumulative_prior: bool
    global_offset: int
    global_percentage: float
    segment_offset: int
    segment_percentage: float
    context: str
