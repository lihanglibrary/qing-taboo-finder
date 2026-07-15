"""TXT reader with encoding fallbacks."""

from __future__ import annotations

from pathlib import Path

from ..models import LoadedDocument


def read_txt(path: Path) -> LoadedDocument:
    encodings = ("utf-8-sig", "utf-8", "gb18030", "big5")
    last_error: UnicodeDecodeError | None = None
    for encoding in encodings:
        try:
            text = path.read_text(encoding=encoding)
            return LoadedDocument(path=path, text=text, title=path.stem)
        except UnicodeDecodeError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    return LoadedDocument(path=path, text=path.read_text(), title=path.stem)