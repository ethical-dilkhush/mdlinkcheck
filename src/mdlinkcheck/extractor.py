from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from mdlinkcheck.models import ExtractOptions, Link, LinkKind

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
AUTO_LINK_RE = re.compile(r"<((?:https?://)[^>]+)>")


def _classify(raw: str) -> LinkKind:
    if raw.startswith("http://") or raw.startswith("https://"):
        return LinkKind.URL
    if raw.startswith("#"):
        return LinkKind.ANCHOR
    return LinkKind.FILE


def extract_markdown_links(
    text: str,
    source: str,
    base: Path,
) -> Iterable[Link]:
    seen: set[str] = set()
    for pattern in (LINK_RE, AUTO_LINK_RE):
        for match in pattern.finditer(text):
            raw = match.group(1).strip()
            if not raw or raw in seen:
                continue
            seen.add(raw)
            yield Link(source=source, kind=_classify(raw), raw=raw)


def collect_files(root: Path, options: ExtractOptions) -> list[Path]:
    if root.is_file():
        return [root] if options.matches(root) else []
    files = [p for p in root.rglob("*") if p.is_file() and options.matches(p)]
    return sorted(files, key=lambda p: (str(p.parent), p.name))


def extract_links_for_files(
    files: list[Path],
    options: ExtractOptions,
) -> Iterable[Link]:
    for file in files:
        yield from extract_markdown_links(
            file.read_text(encoding="utf-8"),
            source=str(file),
            base=file.parent,
        )
