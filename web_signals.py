"""
Web signals: status pages and engineering blogs.

A public status page means the company has formalised reliability. Recent
incidents on it mean they are feeling pain right now, which is the single most
timely reason to talk to them about observability.

Engineering blogs announce migrations, re-platforming and scaling problems
months before any of it reaches the press.

Both need a domain, which we get free from the company's GitHub org.
Everything here fails soft and returns empty on any error.
"""

import re
import time

import requests
import feedparser

import config

HEADERS = {"User-Agent": config.USER_AGENT}

STATUS_SUBDOMAINS = ["status", "statuspage", "health", "trust"]
STATUS_HOSTS = [
    "https://status.{domain}",
    "https://{slug}.statuspage.io",
    "https://status.{domain}/api/v2/summary.json",
    "https://{slug}.instatus.com",
    "https://{slug}.betteruptime.com",
]

BLOG_PATHS = [
    "https://engineering.{domain}/feed",
    "https://blog.{domain}/feed",
    "https://{domain}/blog/feed",
    "https://{domain}/blog/rss.xml",
    "https://{domain}/feed",
    "https://tech.{domain}/feed",
]

# Blog topics that indicate active infrastructure change
BLOG_TRIGGERS = [
    "migration", "migrating", "kubernetes", "scaling", "scale",
    "observability", "monitoring", "incident", "postmortem", "post-mortem",
    "reliability", "downtime", "outage", "latency", "re-platform",
    "modernization", "modernisation", "multi-region", "cost optimization",
    "infrastructure", "microservices", "platform engineering",
]


def check_status_page(domain):
    """
    Returns {"url": ..., "provider": ..., "recent_incidents": n} or None.
    """
    if not domain:
        return None

    slug = domain.split(".")[0]

    # Statuspage.io exposes a clean JSON summary, so try that first
    for template in ("https://status.{domain}/api/v2/summary.json",
                     "https://{slug}.statuspage.io/api/v2/summary.json"):
        url = template.format(domain=domain, slug=slug)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                incidents = data.get("incidents", []) or []
                return {
                    "url": url.replace("/api/v2/summary.json", ""),
                    "provider": "statuspage",
                    "recent_incidents": len(incidents),
                    "status": (data.get("status") or {}).get("description", ""),
                }
        except Exception:
            pass

    # Otherwise just confirm a status page exists
    for sub in STATUS_SUBDOMAINS:
        url = f"https://{sub}.{domain}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=6,
                                allow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 500:
                return {"url": url, "provider": "unknown",
                        "recent_incidents": 0, "status": ""}
        except Exception:
            continue
    return None


def check_engineering_blog(domain, max_posts=8):
    """
    Returns {"url": ..., "signals": [...], "latest": "..."} or None.
    """
    if not domain:
        return None

    for template in BLOG_PATHS:
        url = template.format(domain=domain)
        try:
            parsed = feedparser.parse(url, agent=config.USER_AGENT)
        except Exception:
            continue

        entries = getattr(parsed, "entries", [])
        if not entries:
            continue

        signals, latest = [], ""
        for entry in entries[:max_posts]:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            blob = f"{title} {summary}".lower()
            if not latest:
                latest = title
            hits = [t for t in BLOG_TRIGGERS if t in blob]
            if hits:
                signals.append({"title": title,
                                "topics": sorted(set(hits))[:3],
                                "link": entry.get("link", "")})
        time.sleep(0.2)
        return {"url": url, "signals": signals[:3], "latest": latest}

    return None


def gather(domain):
    """Convenience wrapper. Returns a dict of readable signal strings."""
    out = {"status_page": None, "blog": None, "signals": []}
    if not domain:
        return out

    status = check_status_page(domain)
    if status:
        out["status_page"] = status
        if status["recent_incidents"] > 0:
            out["signals"].append(
                f"{status['recent_incidents']} recent incident(s) on their status page"
            )
        else:
            out["signals"].append("Public status page, reliability is formalised")

    blog = check_engineering_blog(domain)
    if blog and blog.get("signals"):
        out["blog"] = blog
        top = blog["signals"][0]
        out["signals"].append(
            f"Eng blog on {', '.join(top['topics'])}: {top['title'][:60]}"
        )

    return out
