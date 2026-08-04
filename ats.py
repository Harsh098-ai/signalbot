"""
Job board layer.

Greenhouse, Lever, Ashby, Recruitee and Workable all expose public JSON
endpoints for any company using them. No key, no scraping, no terms violation.
We guess the company's board slug, probe each ATS once, then cache the answer.
"""

import re
import html
import time

import requests

import config

HEADERS = {"User-Agent": config.USER_AGENT, "Accept": "application/json"}


def candidate_slugs(name):
    """Generate plausible board slugs for a company name."""
    base = re.sub(r"[^a-z0-9\s]", "", name.lower()).strip()
    compact = base.replace(" ", "")
    hyphen = base.replace(" ", "-")
    options = [compact, hyphen]
    # Common suffixes Indian startups use on their boards
    for suffix in ("technologies", "tech", "labs", "india", "hq", "inc"):
        options.append(compact + suffix)
    # Drop generic trailing words: "Jar Technologies" -> "jar"
    words = base.split()
    if len(words) > 1 and words[-1] in {"technologies", "technology", "labs", "india", "inc", "solutions"}:
        options.insert(0, "".join(words[:-1]))
    seen, unique = set(), []
    for opt in options:
        if opt and opt not in seen:
            seen.add(opt)
            unique.append(opt)
    return unique[:6]


def _strip_html(text):
    if not text:
        return ""
    text = html.unescape(text)
    return re.sub(r"<[^>]+>", " ", text)


def _normalise(ats, payload):
    """Convert each ATS's response shape into a common job dict."""
    jobs = []

    if ats == "greenhouse":
        for j in payload.get("jobs", []):
            jobs.append({
                "id": j.get("id"),
                "title": j.get("title", ""),
                "location": (j.get("location") or {}).get("name", ""),
                "description": _strip_html(j.get("content", "")),
                "url": j.get("absolute_url", ""),
                "posted": j.get("updated_at", ""),
            })

    elif ats == "lever":
        for j in payload if isinstance(payload, list) else []:
            jobs.append({
                "id": j.get("id"),
                "title": j.get("text", ""),
                "location": (j.get("categories") or {}).get("location", ""),
                "description": _strip_html(j.get("descriptionPlain") or j.get("description", "")),
                "url": j.get("hostedUrl", ""),
                "posted": j.get("createdAt", ""),
            })

    elif ats == "ashby":
        for j in payload.get("jobs", []):
            jobs.append({
                "id": j.get("id"),
                "title": j.get("title", ""),
                "location": j.get("location", ""),
                "description": _strip_html(j.get("descriptionPlain") or j.get("descriptionHtml", "")),
                "url": j.get("jobUrl", ""),
                "posted": j.get("publishedAt", ""),
            })

    elif ats == "recruitee":
        for j in payload.get("offers", []):
            jobs.append({
                "id": j.get("id"),
                "title": j.get("title", ""),
                "location": j.get("location", ""),
                "description": _strip_html(j.get("description", "")),
                "url": j.get("careers_url", ""),
                "posted": j.get("published_at", ""),
            })

    elif ats == "workable":
        for j in payload.get("jobs", []):
            jobs.append({
                "id": j.get("shortcode"),
                "title": j.get("title", ""),
                "location": j.get("location", {}).get("city", "") if isinstance(j.get("location"), dict) else "",
                "description": _strip_html(j.get("description", "")),
                "url": j.get("url", ""),
                "posted": j.get("published_on", ""),
            })

    return [j for j in jobs if j.get("title")]


def fetch_jobs(ats, slug):
    """Fetch and normalise jobs for a known ATS and slug. Returns [] on failure."""
    url = config.ATS_ENDPOINTS[ats].format(slug=slug)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=config.REQUEST_TIMEOUT)
        if resp.status_code != 200:
            return []
        return _normalise(ats, resp.json())
    except Exception:
        return []


def resolve(company_name, known_ats=None, known_slug=None, verbose=False):
    """
    Find which ATS a company uses. If already known, skip straight to fetching.
    Returns (ats, slug, jobs).
    """
    if known_ats and known_slug:
        jobs = fetch_jobs(known_ats, known_slug)
        if jobs:
            return known_ats, known_slug, jobs

    for slug in candidate_slugs(company_name):
        for ats in config.ATS_ENDPOINTS:
            jobs = fetch_jobs(ats, slug)
            if jobs:
                if verbose:
                    print(f"    matched {company_name} -> {ats}/{slug} ({len(jobs)} roles)")
                return ats, slug, jobs
            time.sleep(0.15)  # rate limit courtesy

    return None, None, []
