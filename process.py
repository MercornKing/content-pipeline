#!/usr/bin/env python3
"""
process.py — WorkSmart Reviews pipeline processor
Converts .docx files in /drafts to Markdown in /articles,
injects affiliate links, then auto-updates the ARTICLES array in
content/site.js so new articles go live without any manual editing.

Folder structure:
    drafts/           <- drop .docx files here
    articles/         <- processed .md files (served by Netlify)
    content/          <- site files: index.html, site.js, site.css
    affiliate_links.json
    topic_map.json    <- optional: maps slug keywords to topic keys

Usage:
    python process.py                  # process all new drafts
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

# Paths
ROOT         = Path(__file__).parent
DRAFTS_DIR   = ROOT / "drafts"
ARTICLES_DIR = ROOT / "articles"
SITE_JS      = ROOT / "content" / "site.js"
LINKS_FILE   = ROOT / "affiliate_links.json"
TOPIC_MAP    = ROOT / "topic_map.json"
LOG_FILE     = ROOT / "pipeline.log"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# Topic keyword defaults
DEFAULT_TOPIC_KEYWORDS = {
    "marketing":    ["email", "marketing", "mailchimp", "mailerlite", "brevo", "newsletter", "seo", "social"],
    "productivity": ["monday", "asana", "notion", "trello", "clickup", "project", "task", "productivity", "crm"],
    "coaching":     ["coach", "coaching", "scheduling", "calendly", "acuity", "tidycal", "booking"],
    "finance":      ["accounting", "invoic", "bookkeep", "payroll", "tax", "vat", "xero", "quickbooks", "sage", "sole trader"],
    "hr":           ["hr", "hiring", "recruit", "payslip", "employee", "staff", "onboard"],
}

def load_affiliate_links():
    if not LINKS_FILE.exists():
        log.warning("affiliate_links.json not found — no links injected.")
        return {}
    with LINKS_FILE.open() as f:
        raw = json.load(f)
    return {k.lower(): v for k, v in raw.items() if not k.startswith("_")}

def infer_topic(slug, title):
    keywords = dict(DEFAULT_TOPIC_KEYWORDS)
    if TOPIC_MAP.exists():
        with TOPIC_MAP.open() as f:
            keywords.update(json.load(f))
    haystack = (slug + " " + title).lower()
    for topic, kws in keywords.items():
        if any(kw in haystack for kw in kws):
            return topic
    return "general"

def title_to_excerpt(first_para):
    clean = re.sub(r"[#*_`]", "", first_para).strip()
    if len(clean) <= 160:
        return clean
    return clean[:160].rsplit(" ", 1)[0] + "..."

def docx_to_markdown(docx_path):
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
    return re.sub(r"\n{3,}", "\n\n", md).strip()

def inject_affiliate_links(markdown, links):
    warnings = []
    lines = markdown.split("\n")
    output = []
    for i, line in enumerate(lines):
        if "[AFFILIATE LINK]" in line:
            context = (lines[i - 1] + " " + line).lower() if i > 0 else line.lower()
            matched_url = matched_key = None
            for key in sorted(links.keys(), key=len, reverse=True):
                if key in context:
                    matched_url = links[key]
                    matched_key = key
                    break
            if matched_url:
                line = line.replace("[AFFILIATE LINK]", matched_url)
                log.info(f"  Injected '{matched_key}' on line {i + 1}")
            else:
                msg = f"Line {i + 1}: no match for [AFFILIATE LINK] near: '{context[:80]}'"
                warnings.append(msg)
                log.warning(f"  {msg}")
        output.append(line)
    return "\n".join(output), warnings

def add_frontmatter(markdown, source_filename, topic, excerpt, date):
    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else source_filename
    safe_excerpt = excerpt.replace('"', '\\"')
    fm = f'---\ntitle: "{title}"\ndate: {date}\ntopic: {topic}\nexcerpt: "{safe_excerpt}"\nsource: "{source_filename}"\n---\n\n'
    return fm + markdown

def update_site_js(slug, title, topic, excerpt, date):
    if not SITE_JS.exists():
        log.warning(f"  site.js not found — skipping index update")
        return False
    js_text = SITE_JS.read_text(encoding="utf-8")

    # Check if already registered
    if f"slug: '{slug}'" in js_text:
        log.info(f"  site.js already has '{slug}' — skipping")
        return True

    safe_title   = title.replace("'", "\\'")
    safe_excerpt = excerpt.replace('"', '\\"')
    new_entry = (
        f"  {{\n"
        f"    slug: '{slug}',\n"
        f"    title: '{safe_title}',\n"
        f"    topic: '{topic}',\n"
        f"    excerpt: \"{safe_excerpt}\",\n"
        f"    date: '{date}',\n"
        f"  }}"
    )

    # Find the closing ]; of the ARTICLES array and insert before it
    updated = re.sub(
        r"(const ARTICLES\s*=\s*\[)([\s\S]*?)(\];)",
        lambda m: m.group(1) + m.group(2).rstrip("\n") + ",\n" + new_entry + "\n];",
        js_text
    )

    if updated == js_text:
        log.warning("  Could not find ARTICLES array in site.js")
        return False

    SITE_JS.write_text(updated, encoding="utf-8")
    log.info(f"  Updated site.js with '{slug}'")
    return True

def process_file(docx_path, links, force=False):
    slug = re.sub(r"[^a-z0-9]+", "-", docx_path.stem.lower()).strip("-")
    out_path = ARTICLES_DIR / f"{slug}.md"

    if out_path.exists() and not force:
        log.info(f"Skipping '{docx_path.name}' — already processed")
        return True

    log.info(f"Processing: {docx_path.name}")
    try:
        markdown = docx_to_markdown(docx_path)
    except Exception as e:
        log.error(f"  Conversion failed: {e}")
        return False

    markdown, warnings = inject_affiliate_links(markdown, links)

    title_match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else slug.replace("-", " ").title()
    topic = infer_topic(slug, title)
    date  = datetime.now().strftime("%Y-%m-%d")
    paras = [l.strip() for l in markdown.split("\n") if l.strip() and not l.startswith("#")]
    excerpt = title_to_excerpt(paras[0] if paras else title)

    markdown = add_frontmatter(markdown, docx_path.name, topic, excerpt, date)
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    log.info(f"  Written to articles/{slug}.md")

    update_site_js(slug, title, topic, excerpt, date)

    if warnings:
        log.warning(f"  {len(warnings)} unmatched [AFFILIATE LINK] placeholder(s)")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--file", type=str)
    args = parser.parse_args()

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    links = load_affiliate_links()
    log.info(f"Loaded {len(links)} affiliate link(s)")

    files = [DRAFTS_DIR / args.file] if args.file else sorted(DRAFTS_DIR.glob("*.docx"))
    if not files:
        log.info("No .docx files in /drafts — nothing to do.")
        sys.exit(0)

    log.info(f"Found {len(files)} file(s)")
    results = [process_file(f, links, force=args.force) for f in files]
    ok = sum(results)
    log.info(f"Done — {ok} succeeded, {len(results)-ok} failed")
    if len(results) - ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
