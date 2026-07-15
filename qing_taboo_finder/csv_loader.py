"""CSV loading and normalization."""

from __future__ import annotations

import csv
from pathlib import Path

from .constants import CSV_COLUMNS
from .models import EmperorRecord


def split_semicolon_values(raw_value: str) -> list[str]:
    if not raw_value:
        return []
    parts = [part.strip() for part in raw_value.replace("；", ";").split(";")]
    return [part for part in parts if part]


def _read_text_with_fallbacks(csv_path: Path) -> str:
    encodings = ("utf-8-sig", "utf-8", "gb18030", "big5")
    last_error: UnicodeDecodeError | None = None
    for encoding in encodings:
        try:
            return csv_path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return csv_path.read_text()


def load_emperor_records(
    csv_path: str | Path,
) -> list[EmperorRecord]:
    source_path = Path(csv_path)
    text = _read_text_with_fallbacks(source_path)
    rows = list(csv.reader(text.splitlines()))
    records: list[EmperorRecord] = []

    for raw_row in rows[1:]:
        if not raw_row or not any(cell.strip() for cell in raw_row):
            continue
        padded = list(raw_row) + [""] * max(0, 12 - len(raw_row))
        emperor = padded[CSV_COLUMNS["emperor"]].strip()
        if not emperor:
            continue
        sequence_text = padded[CSV_COLUMNS["index"]].strip() or "0"
        try:
            sequence = int(sequence_text)
        except ValueError:
            sequence = 0
        records.append(
            EmperorRecord(
                sequence=sequence,
                emperor=emperor,
                name=padded[CSV_COLUMNS["name"]].strip(),
                traditional_name=padded[CSV_COLUMNS["traditional_name"]].strip(),
                taboo_traditional=split_semicolon_values(
                    padded[CSV_COLUMNS["taboo_traditional"]].strip()
                ),
                taboo_simplified=split_semicolon_values(
                    padded[CSV_COLUMNS["taboo_simplified"]].strip()
                ),
                taboo_radical=split_semicolon_values(
                    padded[CSV_COLUMNS["taboo_radical"]].strip()
                ),
                taboo_substitute=split_semicolon_values(
                    padded[CSV_COLUMNS["taboo_substitute"]].strip()
                ),
                proper_noun_simplified=split_semicolon_values(
                    padded[CSV_COLUMNS["proper_noun_simplified"]].strip()
                ),
                proper_noun_traditional=split_semicolon_values(
                    padded[CSV_COLUMNS["proper_noun_traditional"]].strip()
                ),
                original_proper_noun_simplified=split_semicolon_values(
                    padded[CSV_COLUMNS["original_proper_noun_simplified"]].strip()
                ),
                original_proper_noun_traditional=split_semicolon_values(
                    padded[CSV_COLUMNS["original_proper_noun_traditional"]].strip()
                ),
            )
        )

    return records


def build_merged_records(
    base_csv_path: str | Path,
    proper_noun_csv_path: str | Path,
) -> list[EmperorRecord]:
    records = load_emperor_records(base_csv_path)
    merge_proper_nouns(records, proper_noun_csv_path)
    return records


def write_merged_rule_csv(
    output_path: str | Path,
    records: list[EmperorRecord],
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "序号",
        "皇帝",
        "皇帝简体名",
        "皇帝繁体名",
        "避讳1 繁体名单字拆分",
        "避讳2 簡体名单字拆分",
        "避讳3 可能需要避讳的同偏旁字",
        "避讳4 替代字",
        "避讳5 避讳后的专有词汇 简体",
        "避讳6 避諱後的專有詞彙 繁体",
        "避讳7 避讳前的专有词汇 简体",
        "避讳8 避諱前的專有詞彙 繁体",
    ]

    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for record in sorted(records, key=lambda item: item.sequence):
            writer.writerow(
                [
                    record.sequence,
                    record.emperor,
                    record.name,
                    record.traditional_name,
                    ";".join(record.taboo_traditional),
                    ";".join(record.taboo_simplified),
                    ";".join(record.taboo_radical),
                    ";".join(record.taboo_substitute),
                    ";".join(record.proper_noun_simplified),
                    ";".join(record.proper_noun_traditional),
                    ";".join(record.original_proper_noun_simplified),
                    ";".join(record.original_proper_noun_traditional),
                ]
            )

    return destination


def merge_proper_nouns(
    records: list[EmperorRecord],
    proper_noun_csv_path: str | Path | None,
) -> None:
    if proper_noun_csv_path is None:
        return

    source_path = Path(proper_noun_csv_path)
    if not source_path.exists():
        return

    text = _read_text_with_fallbacks(source_path)
    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        return

    by_emperor = {record.emperor: record for record in records}
    for row in rows:
        emperor = (row.get("皇帝") or "").strip()
        if not emperor or emperor not in by_emperor:
            continue
        record = by_emperor[emperor]
        simplified_tokens = split_semicolon_values((row.get("专有词汇 简体") or "").strip())
        traditional_tokens = split_semicolon_values((row.get("專有詞彙 繁体") or "").strip())
        record.proper_noun_simplified = _dedupe_keep_order(
            record.proper_noun_simplified + simplified_tokens
        )
        record.proper_noun_traditional = _dedupe_keep_order(
            record.proper_noun_traditional + traditional_tokens
        )


def _dedupe_keep_order(tokens: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        if token and token not in seen:
            seen.add(token)
            result.append(token)
    return result