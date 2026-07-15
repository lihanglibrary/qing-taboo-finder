"""Static configuration for taboo checking."""

from __future__ import annotations

from itertools import combinations
from collections import OrderedDict


CSV_COLUMNS = {
    "index": 0,
    "emperor": 1,
    "name": 2,
    "traditional_name": 3,
    "taboo_traditional": 4,
    "taboo_simplified": 5,
    "taboo_radical": 6,
    "taboo_substitute": 7,
    "proper_noun_simplified": 8,
    "proper_noun_traditional": 9,
    "original_proper_noun_simplified": 10,
    "original_proper_noun_traditional": 11,
}


REIGN_ORDER = [
    "顺治",
    "康熙",
    "雍正",
    "乾隆",
    "嘉庆",
    "道光",
    "咸丰",
    "同治",
    "光绪",
    "宣统",
]


ATOMIC_CATEGORY_DEFINITIONS = OrderedDict(
    [
        ("繁体", "繁体"),
        ("简体", "简体"),
        ("偏旁", "偏旁"),
        ("替代字", "替代字"),
        ("专有词汇 简体", "专有词汇 简体"),
        ("專有詞彙 繁体", "專有詞彙 繁体"),
        ("原 专有词汇 简体", "原 专有词汇 简体"),
        ("原 專有詞彙 繁体", "原 專有詞彙 繁体"),
    ]
)


CATEGORY_SELECTION_LABELS = {
    "繁体": "避讳1 繁体名单字拆分",
    "简体": "避讳2 簡体名单字拆分",
    "偏旁": "避讳3 可能需要避讳的同偏旁字",
    "替代字": "避讳4 替代字",
    "专有词汇 简体": "避讳5 避讳后的专有词汇 简体",
    "專有詞彙 繁体": "避讳6 避諱後的專有詞彙 繁体",
    "原 专有词汇 简体": "避讳7 避讳前的专有词汇 简体",
    "原 專有詞彙 繁体": "避讳8 避諱前的專有詞彙 繁体",
}


def _build_check_mode_definitions() -> OrderedDict[str, dict[str, list[str] | str]]:
    modes: OrderedDict[str, dict[str, list[str] | str]] = OrderedDict(
        [
            (
                "traditional_only",
                {
                    "label": "只避讳繁体",
                    "categories": ["繁体"],
                },
            ),
            (
                "traditional_simplified",
                {
                    "label": "避讳繁体和简体",
                    "categories": ["繁体", "简体"],
                },
            ),
            (
                "radical_only",
                {
                    "label": "避讳偏旁",
                    "categories": ["偏旁"],
                },
            ),
            (
                "traditional_simplified_radical",
                {
                    "label": "避讳繁体、简体和偏旁",
                    "categories": ["繁体", "简体", "偏旁"],
                },
            ),
            (
                "substitute_only",
                {
                    "label": "避讳替代字",
                    "categories": ["替代字"],
                },
            ),
            (
                "proper_noun_simplified_only",
                {
                    "label": "只避讳专有词汇简体",
                    "categories": ["专有词汇 简体"],
                },
            ),
            (
                "proper_noun_traditional_only",
                {
                    "label": "只避讳专有词汇繁体",
                    "categories": ["專有詞彙 繁体"],
                },
            ),
            (
                "proper_noun_both",
                {
                    "label": "避讳专有词汇简体和繁体",
                    "categories": ["专有词汇 简体", "專有詞彙 繁体"],
                },
            ),
        ]
    )

    category_names = list(ATOMIC_CATEGORY_DEFINITIONS.keys())
    for size in range(2, len(category_names) + 1):
        for category_group in combinations(category_names, size):
            key = "combo_" + "_".join(_slugify(name) for name in category_group)
            if key in modes:
                continue
            label = "组合：" + " + ".join(category_group)
            modes[key] = {
                "label": label,
                "categories": list(category_group),
            }

    return modes


def _slugify(name: str) -> str:
    mapping = {
        "繁体": "traditional",
        "简体": "simplified",
        "偏旁": "radical",
        "替代字": "substitute",
        "专有词汇 简体": "proper_noun_simplified",
        "專有詞彙 繁体": "proper_noun_traditional",
        "原 专有词汇 简体": "original_proper_noun_simplified",
        "原 專有詞彙 繁体": "original_proper_noun_traditional",
    }
    return mapping[name]


CHECK_MODE_DEFINITIONS = _build_check_mode_definitions()


SEGMENT_HEADING_PATTERNS = [
    r"^\s*第[〇零一二三四五六七八九十百千万廿卅\d]+(?:部分|編|编|卷|章|節|节|回|出)\s*.*$",
    r"^\s*(?:卷[〇零一二三四五六七八九十百千万廿卅\d]+|第[〇零一二三四五六七八九十百千万廿卅\d]+卷)\s*.*$",
    r"^\s*[上中下][卷編编册部]\s*.*$",
    r"^\s*[〇零一二三四五六七八九十百千万廿卅\d]+[、\.．]\s*\S.*$",
    r"^\s*(?:楔子|引言|序|序言|前言|后记|後記|附录|附錄)\s*$",
]


CONTEXT_WINDOW = 20
FALLBACK_SEGMENT_LENGTH = 500