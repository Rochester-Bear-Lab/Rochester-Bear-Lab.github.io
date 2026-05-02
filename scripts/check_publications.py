#!/usr/bin/env python3
"""
Check Semantic Scholar for new publications by Yukang Yan and generate
draft _publications/*.html files for any that are not yet in the repo.

Usage:
    python scripts/check_publications.py [--dry-run]

Options:
    --dry-run   Print what would be created without writing any files.

Environment variables:
    S2_API_KEY      Optional Semantic Scholar API key (raises rate limit).
    S2_AUTHOR_ID    Semantic Scholar author ID (default: 10765566).
"""

import os
import sys
import time

# Allow running from repo root: python scripts/check_publications.py
sys.path.insert(0, os.path.dirname(__file__))

from build_existing_index import build_existing_index
from fetch_metadata import fetch_crossref, fetch_s2_papers
from generate_publication_file import generate_shortname, render_publication_file
from slugify import slugify

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLICATIONS_DIR = os.path.join(REPO_ROOT, "_publications")

DEFAULT_AUTHOR_ID = "10765566"


def main():
    dry_run = "--dry-run" in sys.argv
    author_id = os.environ.get("S2_AUTHOR_ID", DEFAULT_AUTHOR_ID)
    api_key = os.environ.get("S2_API_KEY", "")

    print(f"Building index of existing publications from {PUBLICATIONS_DIR} ...")
    existing_dois, existing_title_slugs = build_existing_index(PUBLICATIONS_DIR)
    print(f"  Found {len(existing_dois)} DOIs, {len(existing_title_slugs)} titles indexed.")

    print(f"\nFetching papers for Semantic Scholar author {author_id} ...")
    papers = fetch_s2_papers(author_id, api_key=api_key or None)
    print(f"  Fetched {len(papers)} papers from Semantic Scholar.")

    existing_filenames = set(os.listdir(PUBLICATIONS_DIR))
    new_files = []

    for paper in papers:
        title = paper.get("title", "")
        if not title:
            continue

        year = paper.get("year")
        if not year:
            continue

        ext = paper.get("externalIds", {}) or {}
        doi = (ext.get("DOI") or "").lower().strip()
        title_slug = slugify(title)

        if doi and doi in existing_dois:
            continue
        if title_slug in existing_title_slugs:
            continue

        print(f"\n  New paper detected: {title} ({year})")

        crossref_data = None
        if doi:
            print(f"    Fetching Crossref metadata for DOI {doi} ...")
            crossref_data = fetch_crossref(doi)
            time.sleep(0.5)

        shortname = generate_shortname(title, year, existing_filenames)
        filename = f"{year}-{shortname}.html"
        filepath = os.path.join(PUBLICATIONS_DIR, filename)

        content = render_publication_file(paper, crossref_data)

        if dry_run:
            print(f"    [dry-run] Would create: _publications/{filename}")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"    Created: _publications/{filename}")
            existing_filenames.add(filename)
            if doi:
                existing_dois.add(doi)
            existing_title_slugs.add(title_slug)
            new_files.append(filename)

    print(f"\n{'[dry-run] ' if dry_run else ''}Done. {len(new_files)} new file(s) created.")
    if new_files:
        print("\nCreated files (hidden: true — review before publishing):")
        for f in new_files:
            print(f"  _publications/{f}")
        print(
            "\nNext steps for each file:\n"
            "  1. Fill in venue_url, venue_location, tags\n"
            "  2. Verify venue_tags and type\n"
            "  3. Add thumbnail to assets/publications/SHORTNAME_thumb.png\n"
            "  4. Set hidden: false when ready to publish\n"
            "  5. Commit and push"
        )


if __name__ == "__main__":
    main()
