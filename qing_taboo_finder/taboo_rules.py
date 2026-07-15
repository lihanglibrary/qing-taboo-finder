"""Taboo rule aggregation based on reign accumulation."""

from __future__ import annotations

from .constants import CHECK_MODE_DEFINITIONS, REIGN_ORDER
from .models import EmperorRecord, TabooEntry


CATEGORY_TO_ATTR = {
    "繁体": "taboo_traditional",
    "简体": "taboo_simplified",
    "偏旁": "taboo_radical",
    "替代字": "taboo_substitute",
    "专有词汇 简体": "proper_noun_simplified",
    "專有詞彙 繁体": "proper_noun_traditional",
    "原 专有词汇 简体": "original_proper_noun_simplified",
    "原 專有詞彙 繁体": "original_proper_noun_traditional",
}


def list_selectable_emperors(records: list[EmperorRecord]) -> list[str]:
    seen = {record.emperor for record in records}
    ordered = [name for name in REIGN_ORDER if name in seen or name == "顺治"]
    remaining = sorted(seen - set(ordered))
    return ordered + remaining


def resolve_accumulated_records(
    records: list[EmperorRecord],
    target_emperor: str,
) -> tuple[list[EmperorRecord], str | None]:
    index_by_emperor = {name: position for position, name in enumerate(REIGN_ORDER)}
    if target_emperor not in index_by_emperor:
        raise ValueError(f"未在清代皇帝顺序中找到：{target_emperor}")

    target_index = index_by_emperor[target_emperor]
    kangxi_index = index_by_emperor["康熙"]

    if target_index < kangxi_index:
        return [], "顺治朝通常不作为避讳查验基准，因此本次不纳入避讳累计。"

    valid_reigns = {
        emperor
        for emperor, index in index_by_emperor.items()
        if kangxi_index <= index <= target_index
    }
    selected_records = [record for record in records if record.emperor in valid_reigns]
    selected_records.sort(key=lambda item: index_by_emperor.get(item.emperor, item.sequence))
    return selected_records, None


def build_taboo_entries(
    records: list[EmperorRecord],
    target_emperor: str,
    mode_key: str,
) -> tuple[list[TabooEntry], str | None]:
    if mode_key not in CHECK_MODE_DEFINITIONS:
        raise ValueError(f"未知查验模式：{mode_key}")

    accumulated_records, message = resolve_accumulated_records(records, target_emperor)
    categories = CHECK_MODE_DEFINITIONS[mode_key]["categories"]
    entries: list[TabooEntry] = []

    for record in accumulated_records:
        for category in categories:
            tokens = getattr(record, CATEGORY_TO_ATTR[category])
            unique_tokens = list(dict.fromkeys(tokens))
            for token in unique_tokens:
                entries.append(
                    TabooEntry(
                        token=token,
                        category=category,
                        emperor=record.emperor,
                        source_sequence=record.sequence,
                        is_current_reign=record.emperor == target_emperor,
                    )
                )

    entries.sort(key=lambda item: (-len(item.token), item.source_sequence, item.token))
    return entries, message