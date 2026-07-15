"""Dispatch document readers by suffix."""

from __future__ import annotations

from pathlib import Path

from ..models import LoadedDocument
from .docx_reader import read_docx
from .epub_reader import read_epub
from .txt_reader import read_txt


def load_document(path: str | Path) -> LoadedDocument:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".txt":
        return read_txt(source)
    if suffix == ".docx":
        return read_docx(source)
    if suffix == ".epub":
        return read_epub(source)
    if suffix == ".doc":
        raise ValueError("暂不直接支持 .doc，请先转换为 .docx 后再检测。")
    raise ValueError(f"不支持的文档格式：{source.suffix}")