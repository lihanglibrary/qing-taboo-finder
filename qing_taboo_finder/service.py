"""Shared application service for command-line and desktop interfaces."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from .constants import CHECK_MODE_DEFINITIONS
from .csv_loader import load_emperor_records
from .detector import detect_hits
from .exporter import export_reports
from .models import DetectionHit
from .readers import load_document
from .segmenter import segment_text
from .taboo_rules import build_taboo_entries, list_selectable_emperors


@dataclass(slots=True)
class DetectionResult:
    """The files and summary produced by one detection run."""

    document_path: Path
    csv_path: Path
    emperor: str
    mode_key: str
    message: str | None
    segment_count: int
    entry_count: int
    hits: list[DetectionHit]
    csv_report: Path
    excel_report: Path


def bundled_resource_path(relative_path: str | Path) -> Path:
    """Resolve files included next to a PyInstaller application."""

    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base_path / relative_path


def default_csv_path() -> Path:
    return bundled_resource_path(Path("data") / "qing_taboo.csv")


def selectable_emperors(csv_path: str | Path) -> list[str]:
    return list_selectable_emperors(load_emperor_records(Path(csv_path)))


def run_detection(
    csv_path: str | Path,
    document_path: str | Path,
    emperor: str,
    mode_key: str,
    output_dir: str | Path,
) -> DetectionResult:
    """Run the complete detection workflow and write both report formats."""

    resolved_csv_path = Path(csv_path)
    resolved_document_path = Path(document_path)
    if not resolved_csv_path.is_file():
        raise ValueError(f"未找到合并后 CSV 文件：{resolved_csv_path}")
    if not resolved_document_path.is_file():
        raise ValueError(f"未找到文档：{resolved_document_path}")
    if mode_key not in CHECK_MODE_DEFINITIONS:
        raise ValueError(f"未知查验模式：{mode_key}")

    records = load_emperor_records(resolved_csv_path)
    emperors = list_selectable_emperors(records)
    if emperor not in emperors:
        raise ValueError(f"目标皇帝不在 CSV 数据中：{emperor}")

    entries, message = build_taboo_entries(records, emperor, mode_key)
    document = load_document(resolved_document_path)
    segments = segment_text(document.text)
    hits = detect_hits(document.path.name, len(document.text), segments, entries)
    csv_report, excel_report = export_reports(output_dir, document.path.name, hits)

    return DetectionResult(
        document_path=document.path,
        csv_path=resolved_csv_path,
        emperor=emperor,
        mode_key=mode_key,
        message=message,
        segment_count=len(segments),
        entry_count=len(entries),
        hits=hits,
        csv_report=csv_report,
        excel_report=excel_report,
    )