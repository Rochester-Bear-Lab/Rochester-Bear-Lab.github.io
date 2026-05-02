import glob
import os
import re

import yaml
from slugify import slugify


def build_existing_index(publications_dir):
    """Return (existing_dois, existing_title_slugs) from all _publications/*.html files."""
    existing_dois = set()
    existing_title_slugs = set()

    for filepath in glob.glob(os.path.join(publications_dir, "*.html")):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not match:
            continue

        try:
            fm = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            continue

        if not fm:
            continue

        if fm.get("doi"):
            existing_dois.add(str(fm["doi"]).lower().strip())

        if fm.get("title"):
            existing_title_slugs.add(slugify(str(fm["title"])))

    return existing_dois, existing_title_slugs
