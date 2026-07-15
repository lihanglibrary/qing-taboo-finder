"""EPUB reader."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT, epub

from ..models import LoadedDocument


def read_epub(path: Path) -> LoadedDocument:
    book = epub.read_epub(str(path))
    fragments: list[str] = []

    ordered_items = []
    for spine_entry in book.spine:
        item_id = spine_entry[0]
        if item_id == "nav":
            continue
        item = book.get_item_with_id(item_id)
        if item and item.get_type() == ITEM_DOCUMENT:
            ordered_items.append(item)

    if not ordered_items:
        ordered_items = list(book.get_items_of_type(ITEM_DOCUMENT))

    for item in ordered_items:
        soup = BeautifulSoup(item.get_content(), "html.parser")
        if _is_probably_navigation(item.get_name(), soup):
            continue
        text = soup.get_text("\n", strip=True)
        if text:
            fragments.append(text)

    return LoadedDocument(path=path, text="\n\n".join(fragments), title=path.stem)


def _is_probably_navigation(item_name: str, soup: BeautifulSoup) -> bool:
    normalized_name = item_name.lower()
    if any(keyword in normalized_name for keyword in ("nav", "toc", "contents")):
        return True

    nav_tag = soup.find("nav")
    anchor_count = len(soup.find_all("a"))
    full_text = soup.get_text(" ", strip=True)
    if nav_tag and len(full_text) < 20000:
        return True
    if anchor_count >= 20 and len(full_text) < 3000:
        return True
    return False