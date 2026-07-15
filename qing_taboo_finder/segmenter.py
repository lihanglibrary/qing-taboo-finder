"""Document segmentation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from collections import Counter, defaultdict
from statistics import median
import re

from .constants import FALLBACK_SEGMENT_LENGTH, SEGMENT_HEADING_PATTERNS
from .models import TextSegment


HEADING_REGEXES = [re.compile(pattern) for pattern in SEGMENT_HEADING_PATTERNS]
NUMBER_CHARS = "〇零一二三四五六七八九十百千万廿卅0123456789"
NUMBERED_HEADING_UNITS = (
    "部分|編|编|卷|章|節|节|回|出|部|册|幕|篇|折|集"
)
NUMBERED_TITLE_REGEX = re.compile(
    rf"^第(?P<number>[{NUMBER_CHARS}]+)(?P<unit>{NUMBERED_HEADING_UNITS})"
    r"(?=[\s　:：、,，.。]|$)"
)
MIN_COHERENT_HEADING_COUNT = 3
MIN_NORMAL_SECTION_GAP = 80


@dataclass(slots=True)
class _HeadingCandidate:
    line_index: int
    offset: int
    title: str
    family: str
    broad_only: bool


def is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return False
    return any(pattern.match(stripped) for pattern in HEADING_REGEXES)


def _heading_family(title: str) -> str:
    numbered = NUMBERED_TITLE_REGEX.match(title)
    if numbered:
        return f"第#${numbered.group('unit')}"
    if re.match(rf"^卷[{NUMBER_CHARS}]+", title):
        return "卷#"
    if re.match(r"^[上中下][卷編编册部]", title):
        return title[:2]
    if re.match(rf"^[{NUMBER_CHARS}]+[、.．]", title):
        return "数字列表标题"
    return title


def _collect_heading_candidates(lines: list[str]) -> list[_HeadingCandidate]:
    candidates: list[_HeadingCandidate] = []
    offset = 0
    for line_index, line in enumerate(lines):
        title = line.strip()
        strict_match = is_heading(line)
        broad_match = bool(title and len(title) <= 60 and NUMBERED_TITLE_REGEX.match(title))
        if strict_match or broad_match:
            candidates.append(
                _HeadingCandidate(
                    line_index=line_index,
                    offset=offset,
                    title=title,
                    family=_heading_family(title),
                    broad_only=broad_match and not strict_match,
                )
            )
        offset += len(line)
    return candidates


def _family_median_gap(candidates: list[_HeadingCandidate]) -> float:
    if len(candidates) < 2:
        return 0.0
    return median(
        current.offset - previous.offset
        for previous, current in zip(candidates, candidates[1:])
    )


def _select_coherent_headings(
    candidates: list[_HeadingCandidate],
) -> list[_HeadingCandidate]:
    """Keep candidates that agree with recurring structures in the full text.

    Regexes only propose candidates.  A numbered family must recur and leave
    meaningful body text between headings; dense local enumerations such as
    “第一件…第五件…” are therefore treated as prose rather than sections.
    """
    if not candidates:
        return []

    by_family: dict[str, list[_HeadingCandidate]] = defaultdict(list)
    for candidate in candidates:
        by_family[candidate.family].append(candidate)

    numbered_families = {
        family: items
        for family, items in by_family.items()
        if family.startswith("第#$")
    }
    coherent_families = {
        family
        for family, items in numbered_families.items()
        if len(items) >= MIN_COHERENT_HEADING_COUNT
        and _family_median_gap(items) >= MIN_NORMAL_SECTION_GAP
    }

    # When no repeated structure exists, retain conservative regex matches and
    # discard broad-only guesses. This preserves compatibility for short texts.
    if not coherent_families:
        return [candidate for candidate in candidates if not candidate.broad_only]

    selected: list[_HeadingCandidate] = []
    family_counts = Counter(candidate.family for candidate in candidates)
    for candidate in candidates:
        if candidate.family.startswith("第#$"):
            if candidate.family in coherent_families:
                selected.append(candidate)
            continue

        # Non-numbered headings such as 序、楔子、上卷 remain valid. A lone
        # numeric-list-like item amid a strong chapter sequence is an outlier.
        if candidate.family == "数字列表标题" and family_counts[candidate.family] < 2:
            continue
        selected.append(candidate)

    return selected


def segment_text(text: str) -> list[TextSegment]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    line_segments = _segment_by_headings(normalized)
    if line_segments:
        return _annotate_duplicate_titles(line_segments)
    paragraph_segments = _segment_by_paragraphs(normalized)
    if paragraph_segments:
        return _annotate_duplicate_titles(paragraph_segments)
    return _annotate_duplicate_titles(_segment_by_length(normalized))


def _segment_by_headings(text: str) -> list[TextSegment]:
    lines = text.splitlines(keepends=True)
    if not lines:
        return []

    heading_lines = {
        candidate.line_index
        for candidate in _select_coherent_headings(_collect_heading_candidates(lines))
    }
    if not heading_lines:
        return []

    segments: list[TextSegment] = []
    current_title = "全文"
    current_lines: list[str] = []
    current_start = 0
    offset = 0
    saw_heading = False

    for line_index, line in enumerate(lines):
        if line_index in heading_lines:
            saw_heading = True
            if current_lines and "".join(current_lines).strip():
                segments.append(
                    TextSegment(
                        index=len(segments) + 1,
                        title=current_title,
                        text="".join(current_lines).strip(),
                        start_offset=current_start,
                    )
                )
            current_title = line.strip()
            current_lines = []
            current_start = offset + len(line)
        else:
            current_lines.append(line)
        offset += len(line)

    if current_lines and "".join(current_lines).strip():
        segments.append(
            TextSegment(
                index=len(segments) + 1,
                title=current_title,
                text="".join(current_lines).strip(),
                start_offset=current_start,
            )
        )

    return segments if saw_heading else []


def _segment_by_paragraphs(text: str) -> list[TextSegment]:
    pattern = re.compile(r"\n\s*\n+")
    segments: list[TextSegment] = []
    start = 0

    for index, match in enumerate(pattern.finditer(text), start=1):
        chunk = text[start:match.start()].strip()
        if chunk:
            title = f"自然段 {len(segments) + 1}"
            segments.append(
                TextSegment(
                    index=len(segments) + 1,
                    title=title,
                    text=chunk,
                    start_offset=start,
                )
            )
        start = match.end()

    tail = text[start:].strip()
    if tail:
        segments.append(
            TextSegment(
                index=len(segments) + 1,
                title=f"自然段 {len(segments) + 1}",
                text=tail,
                start_offset=start,
            )
        )
    return segments


def _segment_by_length(text: str) -> list[TextSegment]:
    stripped = text.strip()
    if not stripped:
        return []

    segments: list[TextSegment] = []
    start = 0
    while start < len(text):
        chunk = text[start : start + FALLBACK_SEGMENT_LENGTH].strip()
        if chunk:
            segments.append(
                TextSegment(
                    index=len(segments) + 1,
                    title=f"固定分段 {len(segments) + 1}",
                    text=chunk,
                    start_offset=start,
                )
            )
        start += FALLBACK_SEGMENT_LENGTH
    return segments


def _annotate_duplicate_titles(segments: list[TextSegment]) -> list[TextSegment]:
    title_count: dict[str, int] = {}
    for segment in segments:
        title_count[segment.title] = title_count.get(segment.title, 0) + 1

    title_seen: dict[str, int] = {}
    for segment in segments:
        total = title_count.get(segment.title, 1)
        if total <= 1:
            continue
        seen = title_seen.get(segment.title, 0) + 1
        title_seen[segment.title] = seen
        segment.title = f"{segment.title}（同名第{seen}段，共{total}段）"

    return segments