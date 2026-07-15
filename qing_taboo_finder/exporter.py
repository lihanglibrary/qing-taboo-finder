"""Export detection results."""

from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook

from .models import DetectionHit


REPORT_HEADERS = [
    "文档名",
    "分段序号",
    "分段标题",
    "命中字",
    "命中类别",
    "所属皇帝",
    "皇帝序号",
    "是否前朝累计避讳",
    "全文位置",
    "全文位置百分比",
    "分段位置",
    "分段位置百分比",
    "命中上下文",
]


def export_reports(
    output_dir: str | Path,
    document_name: str,
    hits: list[DetectionHit],
) -> tuple[Path, Path]:
    safe_name = Path(document_name).stem or "report"
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    csv_path = target_dir / f"{safe_name}_避讳查验报告.csv"
    xlsx_path = target_dir / f"{safe_name}_避讳查验报告.xlsx"

    write_csv_report(csv_path, hits)
    write_excel_report(xlsx_path, hits)
    return csv_path, xlsx_path


def write_csv_report(path: Path, hits: list[DetectionHit]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(REPORT_HEADERS)
        for hit in _sort_hits_for_export(hits):
            writer.writerow(_hit_to_row(hit))


def write_excel_report(path: Path, hits: list[DetectionHit]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "避讳查验报告"
    sheet.append(REPORT_HEADERS)
    for hit in _sort_hits_for_export(hits):
        sheet.append(_hit_to_row(hit))
    workbook.save(path)


def _sort_hits_for_export(hits: list[DetectionHit]) -> list[DetectionHit]:
    return sorted(
        hits,
        key=lambda hit: (-hit.emperor_sequence, hit.global_offset, hit.category),
    )


def _hit_to_row(hit: DetectionHit) -> list[str | int]:
    return [
        hit.document_name,
        hit.segment_index,
        hit.segment_title,
        hit.matched_text,
        hit.category,
        hit.emperor,
        hit.emperor_sequence,
        "是" if hit.is_cumulative_prior else "否",
        hit.global_offset,
        f"{hit.global_percentage:.2f}%",
        hit.segment_offset,
        f"{hit.segment_percentage:.2f}%",
        hit.context,
    ]