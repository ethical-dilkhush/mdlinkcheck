from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from mdlinkcheck.models import Link, LinkKind, Problem


HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def heading_text(markdown: str, expected: str) -> str:
    for line in markdown.splitlines():
        match = HEADING_RE.match(line)
        if match:
            return match.group(1).strip()
    return expected


def check_links(
    links: list[Link],
    root: Path,
) -> tuple[list[Problem], list[dict]]:
    problems: list[Problem] = []
    reports: list[dict] = []

    for link in links:
        pushed = False

        if link.kind == LinkKind.URL:
            pushed = _check_http_link(link, reports)
        elif link.kind == LinkKind.ANCHOR:
            pushed = _check_anchor_link(link, root, reports)
        elif link.kind == LinkKind.FILE:
            pushed = _check_file_link(link, root, reports)

        if not pushed:
            problems.append(Problem(link=link, message="Unresolved reference"))

    return problems, reports


def _check_http_link(link: Link, reports: list[dict]) -> bool:
    reports.append({
        "type": "url",
        "raw": link.raw,
        "ok": False,
        "skipped": True,
        "message": "HTTP checking is not supported in offline mode",
    })
    return False


def _check_anchor_link(link: Link, root: Path, reports: list[dict]) -> bool:
    raw = link.raw
    if "#" not in raw:
        return False

    target_str, _, fragment = raw.partition("#")
    if target_str:
        candidate = (root / target_str).resolve()
    else:
        candidate = Path(link.source).resolve()

    if not candidate.exists():
        message = f"Target file not found: {candidate}"
        reports.append({
            "type": "anchor",
            "raw": link.raw,
            "ok": False,
            "message": message,
        })
        return False

    content = candidate.read_text(encoding="utf-8")
    expected = fragment.replace("-", " ")
    present = expected.lower() in content.lower()
    if not present:
        actual = heading_text(content, expected)
        message = f"Anchor not found; closest heading: {actual}"
        reports.append({
            "type": "anchor",
            "raw": link.raw,
            "ok": False,
            "message": message,
        })
        return False

    reports.append({"type": "anchor", "raw": link.raw, "ok": True})
    return True


def _check_file_link(link: Link, root: Path, reports: list[dict]) -> bool:
    candidate = (root / link.raw).resolve()
    if candidate.exists():
        reports.append({"type": "file", "raw": link.raw, "ok": True})
        return True

    message = f"File not found: {candidate}"
    reports.append({
        "type": "file",
        "raw": link.raw,
        "ok": False,
        "message": message,
    })
    return False
