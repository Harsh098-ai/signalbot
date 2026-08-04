"""
GitHub evidence.

Job ads tell you what a company says it uses. Public repositories tell you what
it actually runs. This module reads a company's GitHub organisation and pulls
out hard infrastructure evidence: Terraform, Kubernetes, Docker, monitoring
config, and the languages their infra is written in.

It also returns their website and location, which we reuse for the status page
and engineering blog checks, and to confirm the company is really in India.

Free. GitHub allows 60 unauthenticated requests an hour, which is not enough
for a full run, so set GITHUB_TOKEN. In GitHub Actions this is provided
automatically as secrets.GITHUB_TOKEN, at 5000 requests an hour, at no cost.
"""

import os
import re
import time

import requests

import config

API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN", "")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": config.USER_AGENT,
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

INDIA_CITIES = [
    "india", "bangalore", "bengaluru", "mumbai", "delhi", "gurugram", "gurgaon",
    "noida", "pune", "hyderabad", "chennai", "kolkata", "ahmedabad", "jaipur",
    "kochi", "indore", "chandigarh", "coimbatore",
]

# Repo names that mean the company manages its own infrastructure
INFRA_REPO_PATTERNS = [
    "terraform", "infra", "infrastructure", "k8s", "kubernetes", "helm",
    "charts", "ansible", "pulumi", "devops", "deploy", "platform",
    "monitoring", "observability", "prometheus", "grafana", "alerting",
    "docker", "cicd", "ci-cd", "pipeline", "cluster", "operator",
]

# Languages that only appear when real infra work is happening
INFRA_LANGUAGES = {
    "HCL": "Terraform",
    "Dockerfile": "Docker",
    "Smarty": "Helm templates",
    "Shell": "Ops tooling",
    "Makefile": "Build tooling",
    "Jsonnet": "Config as code",
}

INFRA_TOPICS = [
    "kubernetes", "docker", "terraform", "aws", "gcp", "azure", "devops",
    "observability", "monitoring", "microservices", "sre", "cloud-native",
    "prometheus", "grafana", "opentelemetry", "helm", "serverless",
]


def _get(url, params=None):
    try:
        resp = requests.get(url, params=params, headers=HEADERS,
                            timeout=config.REQUEST_TIMEOUT)
        if resp.status_code == 403:
            return None       # rate limited
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def find_org(company_name):
    """Locate the most plausible GitHub org for a company. Returns login or None."""
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
    if not slug:
        return None

    # Companies rarely use their bare name. Try the common variants directly,
    # which is cheaper and more reliable than search.
    variants = [
        slug, f"{slug}hq", f"{slug}-hq", f"{slug}inc", f"{slug}io",
        f"{slug}tech", f"{slug}labs", f"{slug}-in", f"{slug}india",
        f"{slug}ai", f"get{slug}", f"{slug}app",
    ]
    words = re.sub(r"[^a-z0-9 ]", "", company_name.lower()).split()
    if len(words) > 1:
        variants.insert(1, "-".join(words))
        variants.insert(2, words[0])

    for variant in variants:
        direct = _get(f"{API}/orgs/{variant}")
        if direct and direct.get("login"):
            return direct["login"]

    found = _get(f"{API}/search/users", {"q": f"{company_name} type:org"})
    if not found:
        return None

    for item in (found.get("items") or [])[:3]:
        login = item.get("login", "").lower()
        if slug in login.replace("-", "") or login.replace("-", "") in slug:
            return item["login"]
    return None


def scan(company_name, max_repos=60):
    """
    Returns a dict of evidence, or None if no org was found.

      {
        "org": "hasura",
        "website": "https://hasura.io",
        "domain": "hasura.io",
        "india_confirmed": True,
        "infra_languages": ["Terraform", "Docker"],
        "infra_repos": ["ddn-helm-charts"],
        "topics": ["kubernetes", "aws"],
        "public_repos": 463,
        "evidence": ["Helm charts in public repos", "Terraform in use"],
      }
    """
    org_login = find_org(company_name)
    if not org_login:
        return None

    org = _get(f"{API}/orgs/{org_login}")
    if not org:
        return None

    repos = _get(f"{API}/orgs/{org_login}/repos",
                 {"per_page": min(max_repos, 100), "sort": "pushed"}) or []

    infra_repos, topics, languages = [], set(), {}
    for repo in repos[:max_repos]:
        name = (repo.get("name") or "").lower()
        description = (repo.get("description") or "").lower()

        if any(p in name for p in INFRA_REPO_PATTERNS):
            infra_repos.append(repo["name"])
        elif any(p in description for p in INFRA_REPO_PATTERNS):
            infra_repos.append(repo["name"])

        for topic in (repo.get("topics") or []):
            if topic in INFRA_TOPICS:
                topics.add(topic)

        lang = repo.get("language")
        if lang:
            languages[lang] = languages.get(lang, 0) + 1

    infra_languages = sorted({
        INFRA_LANGUAGES[lang] for lang in languages if lang in INFRA_LANGUAGES
    })

    website = (org.get("blog") or "").strip()
    domain = ""
    if website:
        domain = re.sub(r"^https?://(www\.)?", "", website).split("/")[0]

    location = (org.get("location") or "").lower()
    india_confirmed = any(city in location for city in INDIA_CITIES)

    evidence = []
    if any("helm" in r.lower() or "chart" in r.lower() for r in infra_repos):
        evidence.append("Helm charts in public repos, so Kubernetes in production")
    if "Terraform" in infra_languages:
        evidence.append("Terraform code public, infrastructure as code in place")
    if "Docker" in infra_languages:
        evidence.append("Dockerfiles public, containerised workloads")
    if any(t in topics for t in ("kubernetes", "observability", "monitoring")):
        evidence.append(f"Repo topics include {', '.join(sorted(topics)[:3])}")
    if infra_repos and not evidence:
        evidence.append(f"Infra repos public ({', '.join(infra_repos[:2])})")

    time.sleep(0.1)

    return {
        "org": org_login,
        "website": website,
        "domain": domain,
        "india_confirmed": india_confirmed,
        "location": org.get("location") or "",
        "infra_languages": infra_languages,
        "infra_repos": infra_repos[:6],
        "topics": sorted(topics),
        "public_repos": org.get("public_repos", 0),
        "evidence": evidence,
    }


def rate_limit_remaining():
    data = _get(f"{API}/rate_limit")
    if not data:
        return 0
    return data.get("resources", {}).get("core", {}).get("remaining", 0)
