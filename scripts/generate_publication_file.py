import re

from slugify import slugify

from fetch_metadata import (
    build_bibtex,
    infer_venue_tags,
    normalize_venue,
)

STOP_WORDS = {
    "a", "an", "the", "of", "in", "on", "for", "to", "and", "or", "with",
    "via", "by", "from", "at", "is", "are", "be", "as", "its", "into",
    "using", "based", "towards", "toward", "through", "between", "across",
    "during", "under", "over", "how", "when", "where", "what", "which",
    "this", "that", "does",
}


def generate_shortname(title, year, existing_filenames):
    """Derive a short filename slug from the paper title, collision-safe."""
    words = re.findall(r"[A-Za-z0-9]+", title)
    significant = [w for w in words if w.lower() not in STOP_WORDS]

    # Prefer camelCase / mixed-case tokens (likely project names like "MineXR")
    project_words = [w for w in significant if re.search(r"[A-Z]", w[1:]) or re.search(r"\d", w)]
    candidate_words = project_words if project_words else significant

    slug = slugify("".join(candidate_words[:2]))[:15]
    if not slug:
        slug = slugify(title)[:15]

    base_slug = slug
    suffix = 2
    while f"{year}-{slug}.html" in existing_filenames:
        slug = f"{base_slug}{suffix}"
        suffix += 1

    return slug


def _format_authors_yaml(authors):
    return "\n".join(f"  - {a}" for a in authors)


def _get_authors(paper, crossref_data):
    """Return author list preferring Crossref (more complete) over S2."""
    if crossref_data:
        cr_authors = crossref_data.get("author", [])
        names = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in cr_authors
            if a.get("family")
        ]
        if names:
            return names

    s2_authors = paper.get("authors", [])
    return [a.get("name", "") for a in s2_authors if a.get("name")]


def _get_month(paper, crossref_data):
    if crossref_data:
        for date_field in ("published", "published-print", "created"):
            date = crossref_data.get(date_field, {})
            parts = date.get("date-parts", [[]])[0] if date else []
            if len(parts) >= 2:
                return f"{parts[1]:02d}"

    pub_date = paper.get("publicationDate", "")
    if pub_date and len(pub_date) >= 7:
        try:
            return f"{int(pub_date[5:7]):02d}"
        except ValueError:
            pass
    return "01"


def _get_doi(paper):
    ext = paper.get("externalIds", {}) or {}
    return ext.get("DOI", "")


def _get_link(doi, paper):
    if doi:
        return f"https://doi.org/{doi}"
    ext = paper.get("externalIds", {}) or {}
    arxiv = ext.get("ArXiv", "")
    if arxiv:
        return f"https://arxiv.org/abs/{arxiv}"
    return ""


def _get_pub_type(crossref_data):
    if not crossref_data:
        return ["Conference"]
    cr_type = crossref_data.get("type", "")
    if cr_type == "journal-article":
        return ["Journal"]
    return ["Conference"]


def _escape_yaml_string(s):
    """Escape a string for use inside YAML double quotes."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render_publication_file(paper, crossref_data):
    """Render the full content of a _publications/YYYY-SHORTNAME.html file."""
    year = paper.get("year") or "YYYY"
    month = _get_month(paper, crossref_data)
    title = paper.get("title", "Untitled")
    authors = _get_authors(paper, crossref_data)
    doi = _get_doi(paper)
    link = _get_link(doi, paper)
    venue_raw = paper.get("venue", "") or ""
    venue = normalize_venue(venue_raw) or venue_raw
    venue_tags = infer_venue_tags(venue)
    pub_type = _get_pub_type(crossref_data)
    bibtex = build_bibtex(crossref_data, doi) if doi else ""
    abstract = (paper.get("abstract") or "").strip()

    authors_yaml = _format_authors_yaml(authors)
    venue_tags_yaml = (
        "\n".join(f"  - {t}" for t in venue_tags) if venue_tags else "  []"
    )
    type_yaml = "\n".join(f"  - {t}" for t in pub_type)
    title_escaped = _escape_yaml_string(title)

    bibtex_block = ""
    if bibtex:
        bibtex_escaped = bibtex.replace('"', '\\"')
        bibtex_block = f'\nbibtex: "{bibtex_escaped}"\n'
    else:
        bibtex_block = "\n# bibtex:  # TODO: add bibtex\n"

    link_line = f"link: {link}" if link else "link:  # TODO: add link"
    doi_line = f"doi: {doi}" if doi else "# doi:  # TODO: add DOI"

    venue_tags_section = (
        f"venue_tags:\n{venue_tags_yaml}"
        if venue_tags
        else "venue_tags:  # TODO: fill in (e.g. CHI, UIST)"
    )

    front_matter = f"""---
layout: publication
year: {year}
month: {month}
selected: false
coming-soon: false
hidden: true
{link_line}
pdf:  # TODO: add direct PDF URL if available
title: "{title_escaped}"
authors:
{authors_yaml}
{doi_line}
venue_location: ""  # TODO: fill in (e.g. "Honolulu, HI, USA")
venue_url: ""  # TODO: fill in
{venue_tags_section}
type:
{type_yaml}
tags: []  # TODO: add lab taxonomy tags (e.g. Augmented Reality, Sensing)
venue: {venue}

#video-thumb:  # TODO: add YouTube ID when available
#video-30sec:
#video-suppl:
#video-talk-5min:
#video-talk-15min:
{bibtex_block}---"""

    body = f"\n{abstract}\n" if abstract else "\n"

    return front_matter + body
