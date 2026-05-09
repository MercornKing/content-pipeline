#!/usr/bin/env python3
"""
process.py — Draft pipeline processor
Converts .docx files in /drafts to Markdown in /content,
injecting affiliate links from affiliate_links.json.

Usage:
    python process.py                  # process all unprocessed drafts
    python process.py --force          # reprocess all drafts
    python process.py --file foo.docx  # process a single file
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

import docx
from markdownify import markdownify

# ── Paths ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
DRAFTS_DIR = ROOT / "drafts"
CONTENT_DIR = ROOT / "content"
LINKS_FILE = ROOT / "affiliate_links.json"
LOG_FILE = ROOT / "pipeline.log"

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_affiliate_links() -> dict:
    """Load and normalise the affiliate links lookup table."""
    if not LINKS_FILE.exists():
        log.warning("affiliate_links.json not found — no links will be injected.")
        return {}
    with LINKS_FILE.open() as f:
        raw = json.load(f)
    # strip the comment key, lower-case all keys
    return {k.lower(): v for k, v in raw.items() if not k.startswith("_")}


def docx_to_markdown(docx_path: Path) -> str:
    """
    Convert a .docx file to Markdown.
    Uses python-docx to extract structured text, then markdownify
    to clean it up. Falls back to plain paragraph extraction if needed.
    """
    doc = docx.Document(str(docx_path))
    html_parts = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            html_parts.append("<br>")
            continue

        style = para.style.name.lower()

        if style.startswith("heading 1"):
            html_parts.append(f"<h1>{text}</h1>")
        elif style.startswith("heading 2"):
            html_parts.append(f"<h2>{text}</h2>")
        elif style.startswith("heading 3"):
            html_parts.append(f"<h3>{text}</h3>")
        else:
            # Preserve bold/italic runs
            line = ""
            for run in para.runs:
                t = run.text
                if run.bold and run.italic:
                    t = f"<strong><em>{t}</em></strong>"
                elif run.bold:
                    t = f"<strong>{t}</strong>"
                elif run.italic:
                    t = f"<em>{t}</em>"
                line += t
            html_parts.append(f"<p>{line}</p>")

    # Also process tables
    for table in doc.tables:
        html_parts.append("<table>")
        for i, row in enumerate(table.rows):
            html_parts.append("<tr>")
            tag = "th" if i == 0 else "td"
            for cell in row.cells:
                html_parts.append(f"<{tag}>{cell.text.strip()}</{tag}>")
            html_parts.append("</tr>")
        html_parts.append("</table>")

    raw_html = "\n".join(html_parts)
    md = markdownify(raw_html, heading_style="ATX", bullets="-")

    # Clean up excess blank lines
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def inject_affiliate_links(markdown: str, links: dict) -> tuple[str, list]:
    """
    Replace [AFFILIATE LINK] placeholders with real URLs.

    Strategy: look at the line containing [AFFILIATE LINK] and
    the line immediately before it for a recognisable product name,
    then substitute the best matching URL.

    Returns (processed_markdown, list_of_warnings).
    """
    warnings = []
    lines = markdown.split("\n")
    output = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if "[AFFILIATE LINK]" in line:
            # Gather context: current line + previous line
            context = line
            if i > 0:
                context = lines[i - 1] + " " + line
            context_lower = context.lower()

            # Find the best matching affiliate key
            matched_url = None
            matched_key = None
            # Sort by length descending so "acuity scheduling" beats "acuity"
            for key in sorted(links.keys(), key=len, reverse=True):
                if key in context_lower:
                    matched_url = links[key]
                    matched_key = key
                    break

            if matched_url:
                new_line = line.replace("[AFFILIATE LINK]", matched_url)
                log.info(f"  ✓ Injected '{matched_key}' link on line {i + 1}")
            else:
                new_line = line  # leave placeholder intact
                msg = f"Line {i + 1}: could not match [AFFILIATE LINK] — no product found in context: '{context[:80]}'"
                warnings.append(msg)
                log.warning(f"  ✗ {msg}")

            output.append(new_line)

        else:
            output.append(line)

        i += 1

    return "\n".join(output), warnings


def add_frontmatter(markdown: str, source_filename: str) -> str:
    """Prepend basic YAML frontmatter for static site generators."""
    # Extract title from first H1
    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else source_filename

    today = datetime.now().strftime("%Y-%m-%d")
    frontmatter = f"""---
title: "{title}"
date: {today}
source: "{source_filename}"
---

"""
    return frontmatter + markdown


def process_file(docx_path: Path, links: dict, force: bool = False) -> bool:
    """Process a single .docx file. Returns True on success."""
    stem = docx_path.stem
    out_path = CONTENT_DIR / f"{stem}.md"

    if out_path.exists() and not force:
        log.info(f"Skipping '{docx_path.name}' — output already exists (use --force to reprocess)")
        return True

    log.info(f"Processing: {docx_path.name}")

    try:
        markdown = docx_to_markdown(docx_path)
    except Exception as e:
        log.error(f"  Failed to convert '{docx_path.name}': {e}")
        return False

    markdown, warnings = inject_affiliate_links(markdown, links)

    markdown = add_frontmatter(markdown, docx_path.name)

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")

    log.info(f"  → Written to {out_path.relative_to(ROOT)}")
    if warnings:
        log.warning(f"  {len(warnings)} unmatched placeholder(s) — update affiliate_links.json")

    return len(warnings) == 0


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Process draft .docx files into Markdown.")
    parser.add_argument("--force", action="store_true", help="Reprocess already-converted files")
    parser.add_argument("--file", type=str, help="Process a single file by name")
    args = parser.parse_args()

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    links = load_affiliate_links()
    log.info(f"Loaded {len(links)} affiliate link(s)")

    if args.file:
        target = DRAFTS_DIR / args.file
        if not target.exists():
            log.error(f"File not found: {target}")
            sys.exit(1)
        files = [target]
    else:
        files = sorted(DRAFTS_DIR.glob("*.docx"))
        if not files:
            log.info("No .docx files found in /drafts — nothing to do.")
            sys.exit(0)

    log.info(f"Found {len(files)} file(s) to process")
    results = [process_file(f, links, force=args.force) for f in files]

    succeeded = sum(results)
    failed = len(results) - succeeded
    log.info(f"Done — {succeeded} succeeded, {failed} failed")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
