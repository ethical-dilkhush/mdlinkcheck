from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from mdlinkcheck.cli import main
from mdlinkcheck.extractor import (
    ExtractOptions,
    collect_files,
    extract_markdown_links,
)
from mdlinkcheck.models import Link, LinkKind, Problem
from mdlinkcheck.scanner import check_links
from mdlinkcheck.writer import write_text_report


def test_extracts_url_link() -> None:
    links = list(
        extract_markdown_links("[text](https://example.com)", "source.md", Path(".")),
    )
    assert [link.raw for link in links] == ["https://example.com"]
    assert links[0].kind == LinkKind.URL


def test_extracts_relative_file_link() -> None:
    links = list(
        extract_markdown_links("[text](next.md)", "src/source.md", Path("src")),
    )
    assert [link.raw for link in links] == ["next.md"]
    assert links[0].kind == LinkKind.FILE


def test_extracts_anchor_link() -> None:
    links = list(extract_markdown_links("[text](#examples)", "source.md", Path(".")))
    assert [link.raw for link in links] == ["#examples"]
    assert links[0].kind == LinkKind.ANCHOR


def test_duplicate_links_de_dupped() -> None:
    text = "[a](https://example.com) and [b](https://example.com)"
    links = list(extract_markdown_links(text, "source.md", Path(".")))
    assert len(links) == 1
    assert links[0].raw == "https://example.com"


def test_empty_markdown_yields_no_links() -> None:
    assert list(extract_markdown_links("", "source.md", Path("."))) == []


def test_collect_files(tmp_path: Path) -> None:
    nested = tmp_path / "docs"
    nested.mkdir()
    (nested / "a.md").write_text("hello", encoding="utf-8")
    (tmp_path / "b.markdown").write_text("world", encoding="utf-8")
    options = ExtractOptions(include_extensions=(".md", ".markdown"))
    files = collect_files(tmp_path, options)
    assert {p.name: p for p in files} == {
        "a.md": tmp_path / "docs" / "a.md",
        "b.markdown": tmp_path / "b.markdown",
    }



def test_collect_single_file(tmp_path: Path) -> None:
    target = tmp_path / "readme.md"
    target.write_text("text", encoding="utf-8")
    assert collect_files(target, ExtractOptions()) == [target]


def test_extension_filter(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("hello", encoding="utf-8")
    (tmp_path / "b.py").write_text("world", encoding="utf-8")
    assert len(collect_files(tmp_path, ExtractOptions())) == 1
    assert collect_files(tmp_path, ExtractOptions())[0].name == "a.md"


def test_file_link_exists(tmp_path: Path) -> None:
    target = tmp_path / "link.md"
    target.write_text("text", encoding="utf-8")
    links = [Link(source="source.md", kind=LinkKind.FILE, raw="link.md")]
    problems, _ = check_links(links, tmp_path)
    assert problems == []


def test_file_link_missing(tmp_path: Path) -> None:
    links = [Link(source="source.md", kind=LinkKind.FILE, raw="missing.md")]
    problems, _ = check_links(links, tmp_path)
    assert len(problems) == 1
    assert problems[0].link.raw == "missing.md"


def test_anchor_link_present(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text("# My Heading\nbody", encoding="utf-8")
    links = [Link(source="source.md", kind=LinkKind.ANCHOR, raw="doc.md#my-heading")]
    problems, _ = check_links(links, tmp_path)
    assert problems == []


def test_anchor_link_missing(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text("# Other Heading\nbody", encoding="utf-8")
    links = [Link(source="source.md", kind=LinkKind.ANCHOR, raw="doc.md#my-heading")]
    problems, reports = check_links(links, tmp_path)
    assert len(problems) == 1
    assert any("Anchor not found" in report.get("message", "") for report in reports)


def test_http_link_returns_unresolved(tmp_path: Path) -> None:
    links = [Link(source="source.md", kind=LinkKind.URL, raw="https://example.com")]
    problems, reports = check_links(links, tmp_path)
    assert len(problems) == 1
    assert "Unresolved reference" in problems[0].message
    assert any(
        report.get("message") == "HTTP checking is not supported in offline mode"
        for report in reports
    )


def test_text_report_capture() -> None:
    buffer = __import__("io").StringIO()
    report = write_text_report([], [], destination=buffer)
    readback = buffer.getvalue()
    assert "No direct link recognition problems found" in report.text
    assert readback == report.text


def test_text_report_with_problems() -> None:
    link = Link(source="source.md", kind=LinkKind.FILE, raw="doc.md")
    problem = Problem(link=link, message="File not found")
    reports = [
        {"type": "file", "raw": "doc.md", "ok": False, "message": problem.message},
    ]
    report = write_text_report([problem], reports)
    assert "Problems: 1" in report.text
    assert "doc.md" in report.text


def test_cli_missing_path_exits_with_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / "missing.md"
    monkeypatch.chdir(str(tmp_path))
    rc = main([str(missing)])
    assert rc == 1


def test_cli_success_returns_zero(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text("# Intro\nbody", encoding="utf-8")
    assert main([str(tmp_path)]) == 0


def test_cli_fatal_returns_one_when_links_broken(tmp_path: Path) -> None:
    (tmp_path / "doc.md").write_text(
        "See [missing](missing.md) and [anchor](#not-here).\n",
        encoding="utf-8",
    )
    rc = main([str(tmp_path), "--fatal"])
    assert rc == 1
