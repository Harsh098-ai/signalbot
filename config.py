"""
Configuration for the account signal bot.
Everything here is free to access. No API keys except your own SMTP login.
"""

import os

# ---------------------------------------------------------------------------
# DISCOVERY: where new Indian companies come from
# ---------------------------------------------------------------------------
# All free RSS. Entrackr and Inc42 are the highest signal for Indian funding.
FUNDING_FEEDS = [
    "https://entrackr.com/feed/",
    "https://inc42.com/feed/",
    "https://yourstory.com/feed",
    "https://www.vccircle.com/rss/technology",
    # Google News is a free catch-all. Tune the query as you like.
    "https://news.google.com/rss/search?q=india+startup+raises+funding+when:7d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+saas+company+series+A+OR+series+B+funding+when:7d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=indian+startup+expands+engineering+team+when:14d&hl=en-IN&gl=IN&ceid=IN:en",
]

# Headline patterns that mean "this company just raised money".
# Indian tech press headlines are formulaic, which works in our favour.
FUNDING_VERBS = [
    "raises", "raised", "bags", "secures", "secured", "mops up",
    "picks up", "closes", "lands", "nets", "scores", "receives",
]

# ---------------------------------------------------------------------------
# SIGNAL ENGINE: public ATS job board endpoints (no auth needed)
# ---------------------------------------------------------------------------
ATS_ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=false",
    "recruitee": "https://{slug}.recruitee.com/api/offers/",
    "workable": "https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true",
}

# ---------------------------------------------------------------------------
# SCORING: what actually matters for an observability sale
# ---------------------------------------------------------------------------

# The single strongest buying signal. They are staffing the function that buys you.
RELIABILITY_ROLE_KEYWORDS = [
    "site reliability", "sre", "devops", "platform engineer",
    "infrastructure engineer", "observability", "cloud engineer",
    "production engineer", "systems engineer", "platform engineering",
]

# Leadership hires. Bigger budget authority, longer cycle, worth flagging separately.
LEADERSHIP_ROLE_KEYWORDS = [
    "vp engineering", "vp of engineering", "head of engineering",
    "head of infrastructure", "head of platform", "director of engineering",
    "cto", "chief technology officer", "head of devops", "engineering manager",
]

# Stack keywords inside job descriptions. This is free tech-stack detection.
OBSERVABILITY_STACK = [
    "prometheus", "grafana", "opentelemetry", "otel", "jaeger", "zipkin",
    "elk", "elasticsearch", "loki", "fluentd", "fluent bit", "pagerduty",
    "opsgenie", "cloudwatch", "nagios", "zabbix", "signoz",
]

SCALE_KEYWORDS = [
    "kubernetes", "k8s", "microservices", "distributed systems",
    "multi-region", "high availability", "terraform", "service mesh",
    "istio", "auto-scaling", "high traffic", "low latency", "sla", "slo",
    "incident response", "on-call", "on call", "postmortem",
]

CLOUD_KEYWORDS = ["aws", "gcp", "google cloud", "azure", "amazon web services"]

# Already paying a competitor. Different play: displacement, not greenfield.
COMPETITOR_KEYWORDS = [
    "datadog", "new relic", "newrelic", "dynatrace", "splunk",
    "appdynamics", "sumo logic", "honeycomb", "lightstep",
]

# Weights reflect your stated priority order:
#   1. Funding   2. Tech stack fit   3. Expansion   4. SRE/DevOps hiring
SCORE_WEIGHTS = {
    # 1. Funding, the anchor signal
    "funding_seed": 30,
    "funding_series_a": 45,
    "funding_series_b": 50,
    "funding_series_c": 45,
    "funding_other": 25,

    # 2. Tech stack fit
    "observability_stack": 30,    # running DIY monitoring today
    "competitor_mention": 22,     # already paying someone, displacement play
    "scale_keyword": 6,           # per keyword, capped below
    "cloud": 8,

    # 3. Expansion
    "hiring_surge": 22,
    "leadership_hire": 12,

    # 4. Reliability hiring
    "new_reliability_role": 14,   # per role, capped below
}

SCORE_CAPS = {
    "new_reliability_role": 35,
    "scale_keyword": 30,
}

# Minimum score before an account earns a place in the digest
MIN_SCORE_TO_REPORT = 45

# An account is "qualified" only when we have actually read its job board.
# Funding-only names go to a separate watchlist section so the digest never
# turns into a rewrite of the funding news.
REQUIRE_JOB_BOARD_FOR_QUALIFIED = True
MIN_SCORE_FOR_WATCHLIST = 30

# ---------------------------------------------------------------------------
# HEADCOUNT (your 0 to 1000 requirement)
# ---------------------------------------------------------------------------
HEADCOUNT_CEILING = 1000

# Never surface these. Observability vendors are competitors, not prospects.
EXCLUDE_COMPANIES = [
    "signoz", "grafana", "datadog", "new relic", "dynatrace", "splunk",
    "elastic", "sumo logic", "honeycomb", "lightstep", "chronosphere",
    "middleware", "last9", "levitate",
]

# If a job description shows they already run Datadog, they are an existing
# customer or an active eval, not a fresh account. Flag rather than drop.
OWN_PRODUCT_KEYWORDS = ["datadog", "dd agent", "datadoghq"]

# Funding is your top-ranked signal, so an account cannot reach High priority
# on stack signals alone.
REQUIRE_FUNDING_FOR_HIGH = True

# Check Wikidata for a real employee count. Free, but adds a second or two per
# company. Set False to fall back to funding stage and hiring volume alone.
USE_WIKIDATA = True

# When headcount cannot be confirmed, keep the account but flag it, rather than
# dropping it. Set True to be strict and drop anything unconfirmed.
DROP_UNCONFIRMED_HEADCOUNT = False

MAX_OPEN_ROLES = 150      # crude upper bound, very high volume means large org
EXCLUDE_STAGES = ["series d", "series e", "series f", "series g", "ipo", "pre-ipo"]

# ---------------------------------------------------------------------------
# EMAIL
# ---------------------------------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")          # your gmail address
SMTP_PASS = os.getenv("SMTP_PASS", "")          # gmail app password, not your login password
EMAIL_TO = os.getenv("EMAIL_TO", "tanushree.dutta@datadoghq.com")  # where the digest goes
EMAIL_SUBJECT = "Account signals digest, {date}"

DB_PATH = os.getenv("DB_PATH", "signalbot.db")
REQUEST_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (compatible; AccountSignalBot/1.0)"
