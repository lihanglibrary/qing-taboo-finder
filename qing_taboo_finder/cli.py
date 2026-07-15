"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

from .constants import (
    ATOMIC_CATEGORY_DEFINITIONS,
    CATEGORY_SELECTION_LABELS,
    CHECK_MODE_DEFINITIONS,
)
from .csv_loader import load_emperor_records
from .detector import detect_hits
from .exporter import export_reports
from .readers import load_document
from .segmenter import segment_text
from .taboo_rules import build_taboo_entries, list_selectable_emperors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="清代古籍避讳查验系统")
    parser.add_argument("--csv", help="避讳 CSV 文件路径")
    parser.add_argument("--document", help="待检查文档路径，支持 TXT / DOCX / EPUB")
    parser.add_argument("--emperor", help="目标皇帝")
    parser.add_argument(
        "--mode",
        choices=list(CHECK_MODE_DEFINITIONS.keys()),
        help="查验模式键名",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="报告导出目录，默认 outputs",
    )
    return parser


def normalize_input(value: str) -> str:
    normalized = value.strip()
    if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {'"', "'"}:
        normalized = normalized[1:-1].strip()
    return normalized


def prompt_if_missing(value: str | None, prompt: str) -> str:
    if value:
        return normalize_input(value)
    response = normalize_input(input(prompt))
    if not response:
        raise ValueError("输入不能为空。")
    return response


def prompt_emperor(emperors: list[str]) -> str:
    print("\n可选皇帝：")
    for index, emperor in enumerate(emperors, start=1):
        print(f"  {index}. {emperor}")
    selection = input("请选择目标皇帝序号：").strip()
    if not selection.isdigit():
        raise ValueError("皇帝选择必须是数字序号。")
    selected_index = int(selection)
    if not 1 <= selected_index <= len(emperors):
        raise ValueError("皇帝序号超出范围。")
    return emperors[selected_index - 1]


def prompt_mode() -> str:
    print("\n可选避讳项目：")
    category_names = list(ATOMIC_CATEGORY_DEFINITIONS.keys())
    for index, category_name in enumerate(category_names, start=1):
        print(f"  {index}. {CATEGORY_SELECTION_LABELS[category_name]}")
    print("  快捷输入：1-4（基础单字）、5-6（避讳后专有词）、7-8（避讳前专有词）、1-8 或 全部")
    selection = input("请选择项目（示例：1-4,6 或 全部）：").strip()

    selected_categories = _parse_category_selection(selection, category_names)
    mode_key = _resolve_mode_key_by_categories(selected_categories)
    if mode_key is None:
        raise ValueError("所选项目无法映射为有效查验模式。")
    return mode_key


def _parse_category_selection(
    selection: str,
    category_names: list[str],
) -> list[str]:
    normalized = selection.strip().replace("，", ",")
    if not normalized:
        raise ValueError("查验项目不能为空。")
    if normalized.lower() in {"all", "全部", "*"}:
        return category_names

    raw_parts = [part.strip() for part in normalized.split(",")]
    if any(not part for part in raw_parts):
        raise ValueError("查验项目格式错误，请使用逗号分隔序号或范围。")

    selected_indexes: list[int] = []
    for part in raw_parts:
        if "-" in part:
            start_text, separator, end_text = part.partition("-")
            if not separator or not start_text.isdigit() or not end_text.isdigit():
                raise ValueError("查验范围格式错误，例如：1-4。")
            start_index = int(start_text)
            end_index = int(end_text)
            if start_index > end_index:
                raise ValueError("查验范围的起始序号不能大于结束序号。")
            indexes = range(start_index, end_index + 1)
        elif part.isdigit():
            indexes = [int(part)]
        else:
            raise ValueError("查验项目必须是序号、范围或“全部”。")

        for index in indexes:
            if not 1 <= index <= len(category_names):
                raise ValueError("查验项目序号超出范围。")
            selected_indexes.append(index)

    selected_index_set = set(selected_indexes)
    return [
        name
        for position, name in enumerate(category_names, start=1)
        if position in selected_index_set
    ]


def _resolve_mode_key_by_categories(categories: list[str]) -> str | None:
    for mode_key, mode_definition in CHECK_MODE_DEFINITIONS.items():
        mode_categories = mode_definition["categories"]
        if list(mode_categories) == categories:
            return mode_key
    return None


def summarize_hits(hits: list) -> None:
    total = len(hits)
    current = sum(1 for hit in hits if not hit.is_cumulative_prior)
    prior = total - current
    print("\n查验摘要")
    print(f"  总命中数：{total}")
    print(f"  本朝新增避讳命中：{current}")
    print(f"  前朝累计避讳命中：{prior}")
    preview = hits[:10]
    if preview:
        print("\n前 10 条命中预览：")
        for hit in preview:
            layer = "前朝累计" if hit.is_cumulative_prior else "本朝新增"
            print(
                f"  - [{hit.segment_title}] {hit.matched_text} | {hit.category} | "
                f"{hit.emperor} | {layer} | 位置 {hit.global_offset}"
            )
            print(f"    上下文：{hit.context}")


def run(args: argparse.Namespace) -> int:
    csv_prompt = "请输入合并后 CSV 文件路径（默认：data/qing_taboo.csv）："
    raw_csv_path = normalize_input(args.csv) if args.csv else normalize_input(input(csv_prompt))
    csv_path = Path(raw_csv_path or "data/qing_taboo.csv")
    if not csv_path.exists():
        raise ValueError(f"未找到合并后 CSV 文件：{csv_path}")

    records = load_emperor_records(csv_path)
    emperors = list_selectable_emperors(records)

    document_path = Path(prompt_if_missing(args.document, "请输入待检测文档路径："))
    emperor = normalize_input(args.emperor) if args.emperor else prompt_emperor(emperors)
    if emperor not in emperors:
        raise ValueError(f"目标皇帝不在 CSV 数据中：{emperor}")

    mode_key = normalize_input(args.mode) if args.mode else prompt_mode()
    entries, message = build_taboo_entries(records, emperor, mode_key)
    document = load_document(document_path)
    segments = segment_text(document.text)
    hits = detect_hits(document.path.name, len(document.text), segments, entries)

    print(f"\n文档：{document.path.name}")
    print(f"规则文件：{csv_path}")
    print(f"查验模式：{CHECK_MODE_DEFINITIONS[mode_key]['label']}")
    print(f"分段数：{len(segments)}")
    print(f"启用避讳项数：{len(entries)}")
    if message:
        print(f"提示：{message}")

    summarize_hits(hits)
    csv_report, excel_report = export_reports(
        normalize_input(args.output_dir),
        document.path.name,
        hits,
    )
    print(f"\n已导出 CSV 报告：{csv_report}")
    print(f"已导出 Excel 报告：{excel_report}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return run(args)
    except Exception as exc:  # noqa: BLE001
        print(f"错误：{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())