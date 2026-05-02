import time

import requests

SEMANTIC_SCHOLAR_BASE = "https://api.semanticscholar.org/graph/v1"
CROSSREF_BASE = "https://api.crossref.org/works"
POLITE_UA = "RochesterBearLab/1.0 (mailto:yukang.yan@rochester.edu)"

VENUE_NORMALIZE = {
    "proceedings of the chi conference on human factors in computing systems": "CHI",
    "proceedings of the chi conference": "CHI",
    "chi": "CHI",
    "acm chi": "CHI",
    "uist": "UIST",
    "acm uist": "UIST",
    "acm symposium on user interface software and technology": "UIST",
    "proceedings of the acm on interactive, mobile, wearable and ubiquitous technologies": "ACM IMWUT",
    "acm imwut": "ACM IMWUT",
    "imwut": "ACM IMWUT",
    "ieee transactions on visualization and computer graphics": "TVCG",
    "tvcg": "TVCG",
    "ieee vr": "IEEE VR",
    "ieee conference on virtual reality and 3d user interfaces": "IEEE VR",
    "cscw": "CSCW",
    "proceedings of the acm on human-computer interaction": "CSCW",
    "acm transactions on computer-human interaction": "TOCHI",
    "dis": "DIS",
    "designing interactive systems": "DIS",
    "ismar": "ISMAR",
    "ieee ismar": "ISMAR",
    "ieee international symposium on mixed and augmented reality": "ISMAR",
    "frontiers in virtual reality": "Front. Virtual Real.",
    "frontiers virtual real.": "Front. Virtual Real.",
    "virtual reality & intelligent hardware": "Virtual Reality & IH",
}

VENUE_TO_TAG = {
    "CHI": ["CHI"],
    "UIST": ["UIST"],
    "ACM IMWUT": ["ACM IMWUT"],
    "TVCG": ["TVCG"],
    "IEEE VR": ["IEEE VR"],
    "CSCW": ["CSCW"],
    "TOCHI": ["TOCHI"],
    "DIS": ["DIS"],
    "ISMAR": ["ISMAR"],
}


def normalize_venue(venue_str):
    if not venue_str:
        return venue_str or ""
    key = venue_str.lower().strip()
    return VENUE_NORMALIZE.get(key, venue_str)


def infer_venue_tags(normalized_venue):
    return VENUE_TO_TAG.get(normalized_venue, [])


def fetch_s2_papers(author_id, api_key=None):
    """Fetch all papers for a Semantic Scholar author ID."""
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    fields = "paperId,title,year,authors,venue,externalIds,publicationDate,abstract"
    papers = []
    offset = 0
    limit = 100

    while True:
        url = (
            f"{SEMANTIC_SCHOLAR_BASE}/author/{author_id}/papers"
            f"?fields={fields}&limit={limit}&offset={offset}"
        )
        resp = _get_with_retry(url, headers=headers)
        if resp is None:
            break

        data = resp.json()
        batch = data.get("data", [])
        papers.extend(batch)

        if len(batch) < limit:
            break
        offset += limit
        time.sleep(1)

    return papers


def fetch_crossref(doi):
    """Fetch metadata from Crossref for a given DOI. Returns dict or None."""
    url = f"{CROSSREF_BASE}/{doi}"
    resp = _get_with_retry(url, headers={"User-Agent": POLITE_UA})
    if resp is None:
        return None

    try:
        return resp.json().get("message", {})
    except Exception:
        return None


def build_bibtex(crossref_data, doi):
    """Build a bibtex string from Crossref metadata."""
    if not crossref_data:
        return ""

    pub_type = crossref_data.get("type", "proceedings-article")
    entry_type = "article" if pub_type == "journal-article" else "inproceedings"

    key = doi.replace("/", "_").replace(".", "_")

    authors = crossref_data.get("author", [])
    author_str = " and ".join(
        f"{a.get('family', '')}, {a.get('given', '')}".strip(", ")
        for a in authors
        if a.get("family")
    )

    title = _get_crossref_title(crossref_data)
    year = _get_crossref_year(crossref_data)

    container = ""
    container_titles = crossref_data.get("container-title", [])
    if container_titles:
        container = container_titles[0]

    publisher = crossref_data.get("publisher", "")
    isbn_list = crossref_data.get("ISBN", [])
    isbn = isbn_list[0] if isbn_list else ""

    lines = [f"@{entry_type}{{{key},"]
    if author_str:
        lines.append(f"author = {{{author_str}}},")
    if title:
        lines.append(f"title = {{{title}}},")
    if year:
        lines.append(f"year = {{{year}}},")
    if isbn:
        lines.append(f"isbn = {{{isbn}}},")
    if publisher:
        lines.append(f"publisher = {{{publisher}}},")
    lines.append(f"url = {{https://doi.org/{doi}}},")
    lines.append(f"doi = {{{doi}}},")
    if container:
        field = "journal" if entry_type == "article" else "booktitle"
        lines.append(f"{field} = {{{container}}},")
    lines.append("}")

    return "\n".join(lines)


def _get_crossref_title(data):
    titles = data.get("title", [])
    return titles[0] if titles else ""


def _get_crossref_year(data):
    date = data.get("published", data.get("published-print", data.get("created", {})))
    parts = date.get("date-parts", [[]])[0] if date else []
    return str(parts[0]) if parts else ""


def _get_with_retry(url, headers=None, max_retries=3):
    delay = 2
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, headers=headers or {}, timeout=15)
            if resp.status_code == 200:
                return resp
            if resp.status_code in (429, 503):
                time.sleep(delay)
                delay *= 2
                continue
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                print(f"  Warning: request failed for {url}: {e}")
            time.sleep(delay)
            delay *= 2
    return None
