from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from mdlinkcheck.extractor import ExtractOptions, collect_files, extract_links_for_files
from mdlinkcheck.models import Link, LinkKind
from mdlinkcheck.scanner import check_links
from mdlinkcheck.writer import WriteReport, write_text_report


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be a positive integer.")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mdlinkcheck",
        description="Check Markdown files for broken links and anchors.",
    )
    parser.add_argument("path", type=Path, help="File or directory to scan.")
    parser.add_argument("--ext", default="md", help="Additional file extension to treat as Markdown.")
    parser.add_argument("--exclude-url", default=None, help="Regex of URLs to skip.")
    parser.add_argument("--exclude-file", default=None, help="Regex of file paths to skip.")
    parser.add_argument("--exclude-external", action="store_true", help="Skip all HTTP/HTTPS checks.")
    parser.add_argument("--timeout", type=_positive_int, default=15, help="HTTP request timeout in seconds.")
    parser.add_argument("--concurrency", type=_positive_int, default=10, help="Maximum parallel HTTP requests.")
    parser.add_argument("--output", default=None, help="Write JSON report to this path.")
    parser.add_argument("--fatal", action="store_true", help="Exit with code 1 when direct link problems are found.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    extensions = tuple({ext.strip().lower().lstrip(".") for ext in ("md", args.ext)})
    options = ExtractOptions(include_extensions=tuple(f".{ext or 'md'}" for ext in extensions))

    target = args.path.expanduser().resolve()
    if not target.exists():
        print(f"Path not found: {target}", file=sys.stderr)
        return 1

    files = collect_files(target, options)
    links = list(extract_links_for_files(files, options))
    problems, reports = check_links(links, target)

    if args.output:
        payload = {
            "path": str(target),
            "problems": [
                {
                    "source": problem.link.source,
                    "kind": problem.link.kind.value,
                    "raw": problem.link.raw,
                    "message": problem.message,
                }
                for problem in problems
            ],
            "reports": reports,
        }
        Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        report = write_text_report(problems, reports)
        print(report.text)

    if args.fatal and problems:
        return 1
    return 0
