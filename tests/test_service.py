"""Integration coverage for the shared detection service."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from qing_taboo_finder.service import run_detection


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DetectionServiceTests(unittest.TestCase):
    def test_generates_both_report_formats_for_example_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = run_detection(
                PROJECT_ROOT / "data" / "qing_taboo.csv",
                PROJECT_ROOT / "examples" / "tao_hua_shan_excerpt.txt",
                "道光",
                "combo_traditional_simplified_radical_substitute",
                temporary_directory,
            )

            self.assertGreater(result.segment_count, 0)
            self.assertGreater(result.entry_count, 0)
            self.assertTrue(result.csv_report.is_file())
            self.assertTrue(result.excel_report.is_file())


if __name__ == "__main__":
    unittest.main()