# mdlinkcheck

A lightweight command-line tool that scans Markdown files for broken hyperlinks and cross-references. It checks HTTP/S URLs and relative file links, classifying them so you can triage failures without needing a headless browser.

## About

Markdown documents accumulate links over time. Files move, URLs rot, and anchors get renamed. `mdlinkcheck` walks your Markdown tree and verifies that each link is recognized, classifying it so triage is fast without noisy network fetches.

## Features

- HTTP/S link detection in standard Markdown links and autolinks
- Relative file link detection
- Anchor (`#heading`) detection
- File discovery with configurable extension filters
- JSON report output for CI integration
- Plain stdout text reporting

## Installation

```bash
pip install -e .
```

Run directly from source:

```bash
python -m mdlinkcheck.cli path/to/docs
```

## Usage

Scan the current directory for links to review:

```bash
mdlinkcheck .
```

Scan specific files or directories:

```bash
mdlinkcheck README.md docs/
mdlinkcheck . --ext markdown
```

Write a JSON report:

```bash
mdlinkcheck . --output report.json
```

### Options

- `path` — directory or file to scan
- `--ext md` — additional file extension to treat as Markdown
- `--output <path>` — write JSON instead of printing text
- `--timeout 15` — reserved for future HTTP support
- `--concurrency 10` — reserved for future HTTP support
- `--fatal` — exit non-zero when scan produces unrecognized references

## Project structure

```text
mdlinkcheck/
├── README.md
├── pyproject.toml
├── src/
│   └── mdlinkcheck/
│       ├── __init__.py
│       ├── cli.py
│       ├── extractor.py
│       ├── models.py
│       ├── scanner.py
│       └── writer.py
└── tests/
    ├── __init__.py
    └── test_suite.py
```

## License

MIT
