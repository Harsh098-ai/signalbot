"""
Discovery layer.

Indian tech press writes funding headlines in a very predictable shape:
    "Zepto raises $665 Mn led by ..."
    "Fintech startup Jar bags $22 Mn in Series B"
We exploit that to pull company names out for free, no Crunchbase needed.
"""

import re
import time
import datetime as dt

import feedparser

import config

# Words that appear before a company name and should be stripped off
LEAD_NOISE = re.compile(
    r"^(exclusive|breaking|update|report|india[''`]?s|indian|bengaluru[- ]based|"
    r"mumbai[- ]based|delhi[- ]based|gurugram[- ]based|noida[- ]based|pune[- ]based|"
    r"hyderabad[- ]based|chennai[- ]based|b2b|b2c|saas|fintech|healthtech|edtech|"
    r"agritech|d2c|ai|deeptech|logistics|insurtech|startup|firm|platform|company)\b[\s:,-]*",
    re.IGNORECASE,
)

SECTOR_WORDS = {
    "fintech": "Fintech", "insurtech": "Insurtech", "healthtech": "Healthtech",
    "edtech": "Edtech", "agritech": "Agritech", "d2c": "D2C", "b2b": "B2B",
    "saas": "SaaS", "logistics": "Logistics", "deeptech": "Deeptech",
    "ai": "AI", "ecommerce": "Ecommerce", "e-commerce": "Ecommerce",
    "mobility": "Mobility", "proptech": "Proptech", "gaming": "Gaming",
    "cybersecurity": "Cybersecurity", "spacetech": "Spacetech",
    "cleantech": "Cleantech", "foodtech": "Foodtech", "hrtech": "HRtech",
}

INVESTOR_PATTERN = re.compile(
    r"(?:led by|backed by|from)\s+([A-Z][\w&.\- ]{2,40}?)(?:,| and | in | to |$)",
)

STAGE_PATTERNS = [
    (re.compile(r"\bpre[- ]?seed\b", re.I), "pre-seed"),
    (re.compile(r"\bseed\b", re.I), "seed"),
    (re.compile(r"\bseries\s*a\b", re.I), "series a"),
    (re.compile(r"\bseries\s*b\b", re.I), "series b"),
    (re.compile(r"\bseries\s*c\b", re.I), "series c"),
    (re.compile(r"\bseries\s*d\b", re.I), "series d"),
    (re.compile(r"\bseries\s*e\b", re.I), "series e"),
    (re.compile(r"\bseries\s*f\b", re.I), "series f"),
    (re.compile(r"\bseries\s*g\b", re.I), "series g"),
    (re.compile(r"\bpre[- ]?ipo\b", re.I), "pre-ipo"),
]

AMOUNT_PATTERN = re.compile(
    r"(\$\s?\d[\d,.]*\s?(?:mn|million|bn|billion|k)?|(?:rs|inr|₹)\s?\d[\d,.]*\s?(?:cr|crore|lakh|mn)?)",
    re.I,
)


def _extract_company(title):
    """Pull the company name out of a funding headline."""
    # Headlines stack qualifiers: "SaaS firm Zluri", "Fintech startup Jar".
    # Strip repeatedly until nothing more comes off.
    cleaned = title.strip()
    for _ in range(5):
        stripped = LEAD_NOISE.sub("", cleaned)
        if stripped == cleaned:
            break
        cleaned = stripped
    verbs = "|".join(re.escape(v) for v in config.FUNDING_VERBS)
    match = re.search(rf"^(.{{2,60}}?)\s+(?:{verbs})\b", cleaned, re.IGNORECASE)
    if not match:
        return None

    name = match.group(1).strip(" ,:-|")
    # Strip trailing descriptors: "Jar, a savings app" -> "Jar"
    name = re.split(r",| - | \u2013 ", name)[0].strip()
    # Reject junk
    if len(name) < 2 or len(name.split()) > 4:
        return None
    if name.lower() in {"startup", "company", "firm", "it", "this", "the company"}:
        return None
    return name


def _extract_stage(text):
    for pattern, label in STAGE_PATTERNS:
        if pattern.search(text):
            return label
    return "unknown"


def _extract_amount(text):
    match = AMOUNT_PATTERN.search(text)
    return match.group(1).strip() if match else ""


def _extract_sector(text):
    lowered = text.lower()
    for word, label in SECTOR_WORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            return label
    return ""


def _extract_investors(text):
    match = INVESTOR_PATTERN.search(text)
    return match.group(1).strip() if match else ""


def slugify(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def discover(feeds=None, lookback_days=7, verbose=True):
    """
    Returns a list of dicts:
      {name, slug, funding_stage, funding_amount, funding_url, headline, published}
    """
    feeds = feeds or config.FUNDING_FEEDS
    cutoff = dt.datetime.now() - dt.timedelta(days=lookback_days)
    found = {}

    for url in feeds:
        try:
            parsed = feedparser.parse(url, agent=config.USER_AGENT)
        except Exception as exc:
            if verbose:
                print(f"  feed failed: {url} ({exc})")
            continue

        if verbose:
            print(f"  {len(parsed.entries):>3} entries from {url[:60]}")

        for entry in parsed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            blob = f"{title} {summary}"

            published = None
            if entry.get("published_parsed"):
                published = dt.datetime.fromtimestamp(time.mktime(entry.published_parsed))
                if published < cutoff:
                    continue

            name = _extract_company(title)
            if not name:
                continue

            stage = _extract_stage(blob)
            if stage in config.EXCLUDE_STAGES:
                continue  # too large for a 0 to 1000 headcount target

            key = slugify(name)
            if key in found:
                continue

            found[key] = {
                "name": name,
                "slug": key,
                "funding_stage": stage,
                "funding_amount": _extract_amount(blob),
                "funding_url": entry.get("link", ""),
                "sector": _extract_sector(blob),
                "investors": _extract_investors(title),
                "headline": title,
                "published": published.strftime("%d %b %Y") if published else "",
            }
        time.sleep(0.5)  # be polite

    return list(found.values())


if __name__ == "__main__":
    for company in discover():
        print(f"{company['name']:<28} {company['funding_stage']:<12} {company['funding_amount']}")
