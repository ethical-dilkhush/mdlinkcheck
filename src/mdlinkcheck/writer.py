from __future__ import annotations

from pathlib import Path
from typing import Optional, TextIO

from mdlinkcheck.models import Problem, WriteReport


def write_text_report(
    problems: list[Problem],
    reports: list[dict],
    destination: Optional[TextIO | Path] = None,
) -> WriteReport:
    lines = ["mdlinkcheck report", "=" * 20, ""]
    if not problems:
        lines.append("No direct link recognition problems found.")
    else:
        lines.append(f"Problems: {len(problems)}")
        for problem in problems:
            lines.append(f"- {problem.link.label()}: {problem.message}")

    lines.append("")
    network_skipped = sum(
        1 for report in reports
        if report.get("type") == "url" and not report.get("ok")
    )
    lines.append(
        f"Network checks skipped or reported unresolved: {network_skipped}",
    )

    text = "\n".join(lines)
    if isinstance(destination, Path):
        destination.write_text(text, encoding="utf-8")
    elif destination is not None:
        destination.write(text)

    return WriteReport(text=text)
