"""Detection logic for taboo entries."""

from __future__ import annotations

from .constants import CONTEXT_WINDOW
from .models import DetectionHit, TabooEntry, TextSegment


def detect_hits(
    document_name: str,
    document_length: int,
    segments: list[TextSegment],
    entries: list[TabooEntry],
) -> list[DetectionHit]:
    hits: list[DetectionHit] = []
    for segment in segments:
        for entry in entries:
            if not entry.token:
                continue
            start = 0
            while True:
                position = segment.text.find(entry.token, start)
                if position == -1:
                    break
                global_offset = segment.start_offset + position
                hits.append(
                    DetectionHit(
                        document_name=document_name,
                        segment_index=segment.index,
                        segment_title=segment.title,
                        matched_text=entry.token,
                        category=entry.category,
                        emperor=entry.emperor,
                        emperor_sequence=entry.source_sequence,
                        is_cumulative_prior=not entry.is_current_reign,
                        global_offset=global_offset,
                        global_percentage=compute_percentage(global_offset, document_length),
                        segment_offset=position,
                        segment_percentage=compute_percentage(position, len(segment.text)),
                        context=build_context(segment.text, position, len(entry.token)),
                    )
                )
                start = position + 1
    hits.sort(
        key=lambda item: (
            item.global_offset,
            len(item.matched_text) * -1,
            item.emperor,
            item.category,
        )
    )
    return hits


def build_context(text: str, position: int, token_length: int) -> str:
    left = max(0, position - CONTEXT_WINDOW)
    right = min(len(text), position + token_length + CONTEXT_WINDOW)
    return text[left:right].replace("\n", " ").strip()


def compute_percentage(offset: int, length: int) -> float:
    if length <= 0:
        return 0.0
    return (offset / length) * 100