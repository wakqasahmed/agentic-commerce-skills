#!/usr/bin/env python3
import argparse
import re
from datetime import date
from pathlib import Path


SOURCE_HEADING = re.compile(r"^## (SRC-[A-Z0-9-]+)$", re.MULTILINE)
CITATION = re.compile(r"\[(SRC-[A-Z0-9-]+)\]")
REQUIRED_FIELDS = (
    "Publisher",
    "Official URL",
    "Supported claim",
    "Specification version",
    "Last verified",
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate registered source citations.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    return parser.parse_args()


def parse_ledger(ledger: Path) -> tuple[dict[str, dict[str, str]], int, list[str]]:
    if not ledger.is_file():
        return {}, 0, ["missing SOURCES.md"]

    text = ledger.read_text()
    freshness_match = re.search(r"^Freshness window: (\d+) days\.$", text, re.MULTILINE)
    errors = [] if freshness_match else ["malformed or missing freshness window"]
    freshness_days = int(freshness_match.group(1)) if freshness_match else 0
    headings = list(SOURCE_HEADING.finditer(text))
    entries: dict[str, dict[str, str]] = {}

    for index, heading in enumerate(headings):
        source_id = heading.group(1)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[heading.end() : end]
        fields = dict(re.findall(r"^- ([A-Za-z ]+):\s*(.+)$", body, re.MULTILINE))
        if source_id in entries:
            errors.append(f"duplicate source {source_id}")
        entries[source_id] = fields
        for field in REQUIRED_FIELDS:
            if not fields.get(field):
                errors.append(f"{source_id}: missing {field}")

        url = fields.get("Official URL", "")
        if url and not re.fullmatch(r"https://\S+", url):
            errors.append(f"{source_id}: malformed Official URL")

        verified = fields.get("Last verified", "")
        if verified:
            try:
                date.fromisoformat(verified)
            except ValueError:
                errors.append(f"{source_id}: malformed Last verified date")

    if not headings:
        errors.append("SOURCES.md contains no source entries")
    return entries, freshness_days, errors


def markdown_citations(root: Path) -> set[str]:
    citations: set[str] = set()
    for markdown_file in root.rglob("*.md"):
        if markdown_file.name == "SOURCES.md" or ".git" in markdown_file.parts:
            continue
        citations.update(CITATION.findall(markdown_file.read_text()))
    return citations


def main() -> int:
    root = parse_arguments().root.resolve()
    entries, freshness_days, errors = parse_ledger(root / "SOURCES.md")
    citations = markdown_citations(root)

    for source_id in sorted(citations - entries.keys()):
        errors.append(f"unregistered citation {source_id}")
    for source_id in sorted(entries.keys() - citations):
        errors.append(f"unused source {source_id}")

    today = date.today()
    for source_id, fields in sorted(entries.items()):
        verified = fields.get("Last verified")
        if not verified or not freshness_days:
            continue
        try:
            age = (today - date.fromisoformat(verified)).days
        except ValueError:
            continue
        if age > freshness_days:
            print(f"warning: {source_id} was last verified {age} days ago")

    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1

    print(f"validated {len(entries)} sources and {len(citations)} cited source IDs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
