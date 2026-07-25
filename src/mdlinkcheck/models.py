from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class LinkKind(str, Enum):
    URL = "url"
    FILE = "file"
    ANCHOR = "anchor"


@dataclass(frozen=True)
class Link:
    source: str
    kind: LinkKind
    raw: str

    def label(self) -> str:
        return self.raw


@dataclass(frozen=True)
class Problem:
    link: Link
    message: str

    def label(self) -> str:
        return f"{self.link.label()}: {self.message}"


@dataclass(frozen=True)
class ExtractOptions:
    include_extensions: tuple[str, ...] = (".md",)

    def matches(self, path: Path) -> bool:
        return path.suffix.lower() in self.include_extensions


@dataclass(frozen=True)
class WriteReport:
    text: str
