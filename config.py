"""
Configuration, built around your ICP.

ICP summary
-----------
Geography    India
Size         0 to 1000 employees
Infra        Running production workloads on AWS, Azure or GCP, or actively
             migrating to them. Pure on-prem with no migration intent is out.
Eng team     10 or more engineers, with DevOps, SRE, platform or eng leadership
Budget cue   Fresh funding, IPO, international expansion, cloud migration,
             platform modernisation, or AI workload scaling

Industry priority
-----------------
Tier 1  BFSI, Fintech, Manufacturing              highest value per account
Tier 2  Software, Internet, SaaS                  highest volume
Tier 3  Professional and IT Services, EdTech      third
"""

import os

# ---------------------------------------------------------------------------
# DISCOVERY
# ---------------------------------------------------------------------------
FUNDING_FEEDS = [
    "https://entrackr.com/feed/",
    "https://inc42.com/feed/",
    "https://yourstory.com/feed",
    "https://www.vccircle.com/rss/technology",
    "https://news.google.com/rss/search?q=india+startup+raises+funding+when:7d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+saas+company+series+A+OR+series+B+funding+when:7d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=indian+company+cloud+migration+OR+AWS+OR+Azure+when:14d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=indian+company+expands+engineering+team+OR+global+expansion+when:14d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+company+IPO+listing+technology+when:14d&hl=en-IN&gl=IN&ceid=IN:en",
    # Wider net across your priority industries
    "https://news.google.com/rss/search?q=india+fintech+OR+bfsi+startup+funding+when:14d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+manufacturing+digital+transformation+cloud+when:21d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=indian+company+kubernetes+OR+devops+OR+platform+engineering+when:21d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+startup+AI+infrastructure+GPU+scaling+when:21d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=indian+SaaS+company+US+expansion+when:21d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+bank+OR+nbfc+cloud+migration+AWS+Azure+when:21d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://www.medianama.com/feed/",
    "https://techcrunch.com/tag/india/feed/",
]

# How far back to look for news. Wider window means more companies per run.
DEFAULT_LOOKBACK_DAYS = 14

FUNDING_VERBS = [
    "raises", "raised", "bags", "secures", "secured", "mops up",
    "picks up", "closes", "lands", "nets", "scores", "receives",
]

# ---------------------------------------------------------------------------
# JOB BOARDS (public JSON, no auth)
# ---------------------------------------------------------------------------
ATS_ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=false",
    "recruitee": "https://{slug}.recruitee.com/api/offers/",
    "workable": "https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true",
    # Indian and other platforms. Response shapes are unverified, so these are
    # attempted defensively and simply return nothing if the format differs.
    "smartrecruiters": "https://api.smartrecruiters.com/v1/companies/{slug}/postings",
    "teamtailor": "https://{slug}.teamtailor.com/jobs.json",
    "personio": "https://{slug}.jobs.personio.de/search.json",
    "freshteam": "https://{slug}.freshteam.com/api/job_postings",
}

# ---------------------------------------------------------------------------
# HARD REQUIREMENT 1: cloud-native or cloud-migrating
# ---------------------------------------------------------------------------
CLOUD_PROVIDERS = [
    "aws", "amazon web services", "ec2", "eks", "s3", "lambda", "fargate",
    "azure", "aks", "gcp", "google cloud", "gke", "bigquery", "cloud run",
]

# Managed services are strong evidence, because you only name these if you
# actually run them. A bare "AWS/Azure/GCP" in a requirements list is not.
CLOUD_SERVICES_STRONG = [
    "ec2", "eks", "ecs", "fargate", "s3", "rds", "aurora", "lambda",
    "cloudfront", "aks", "azure functions", "cosmos db", "gke", "cloud run",
    "bigquery", "pub/sub", "cloud sql", "dynamodb", "sqs", "sns", "msk",
]

# Phrases that show the cloud is theirs, not a line on a wish list
CLOUD_OWNERSHIP_PHRASES = [
    "our aws", "our azure", "our gcp", "our cloud", "runs on aws",
    "running on aws", "hosted on aws", "deployed on aws", "our infrastructure on",
    "runs on gcp", "running on gcp", "hosted on gcp", "runs on azure",
    "running on azure", "hosted on azure", "our production", "in production on",
    "workloads on aws", "workloads on gcp", "workloads on azure",
]

# More than this many distinct providers named means it is a requirements list
MAX_CREDIBLE_CLOUD_PROVIDERS = 2

# Actively moving to cloud. Strong budget trigger in its own right.
MIGRATION_KEYWORDS = [
    "cloud migration", "migrating to aws", "migrate to aws", "migration to cloud",
    "lift and shift", "re-platform", "replatform", "modernization",
    "modernisation", "cloud transformation", "moving off on-prem",
    "legacy modernization", "monolith to microservices", "cloud adoption",
    "hybrid cloud", "multi cloud", "multi-cloud",
]

# On-prem only, with no migration language, is out of ICP.
ONPREM_KEYWORDS = [
    "on-premise", "on premise", "on-prem", "bare metal", "colocation",
    "data centre", "data center", "physical servers", "racks",
]

# ---------------------------------------------------------------------------
# HARD REQUIREMENT 2: real engineering org
# ---------------------------------------------------------------------------
RELIABILITY_ROLE_KEYWORDS = [
    "site reliability", "sre", "devops", "platform engineer",
    "infrastructure engineer", "observability", "cloud engineer",
    "production engineer", "systems engineer", "platform engineering",
    "cloud architect", "solutions architect",
]

ENGINEERING_ROLE_KEYWORDS = [
    "engineer", "developer", "architect", "sre", "devops", "backend",
    "full stack", "fullstack", "data engineer", "ml engineer", "qa",
    "technical lead", "tech lead",
]

LEADERSHIP_ROLE_KEYWORDS = [
    "vp engineering", "vp of engineering", "head of engineering",
    "head of infrastructure", "head of platform", "director of engineering",
    "cto", "chief technology officer", "head of devops", "engineering manager",
    "director of technology", "head of technology", "director of infrastructure",
    "engineering director", "platform lead", "head of sre",
]

# Titles that must never count as engineering leadership, however they read.
NON_ENGINEERING_TITLES = [
    "sales", "marketing", "account executive", "customer success",
    "business development", "revenue", "partnerships", "hr ", "people",
    "finance", "recruit", "talent", "legal", "operations manager",
    "content", "brand", "growth marketing", "solutions consultant",
]

MIN_ENGINEERING_ROLES = 3      # open eng roles suggesting a team of 10+

# ---------------------------------------------------------------------------
# PERSONA AND INFRA COMPLEXITY KEYWORDS
# ---------------------------------------------------------------------------
INFRA_COMPLEXITY = [
    "kubernetes", "k8s", "autoscaling", "auto-scaling", "containers",
    "docker", "microservices", "hosts", "infrastructure", "monitoring",
    "distributed systems", "multi-region", "high availability", "terraform",
    "service mesh", "istio", "helm", "ci/cd", "high traffic", "low latency",
    "sla", "slo", "incident response", "on-call", "on call", "postmortem",
    "observability", "apm", "tracing", "logging", "metrics",
]

# Running their own monitoring today. Best possible fit signal.
OBSERVABILITY_STACK = [
    "prometheus", "grafana", "opentelemetry", "otel", "jaeger", "zipkin",
    "elk", "elasticsearch", "loki", "fluentd", "fluent bit", "pagerduty",
    "opsgenie", "cloudwatch", "nagios", "zabbix", "azure monitor",
    "stackdriver", "cloud logging",
]

COMPETITOR_KEYWORDS = [
    "new relic", "newrelic", "dynatrace", "splunk", "appdynamics",
    "sumo logic", "honeycomb", "lightstep", "grafana cloud", "chronosphere",
]

# AI workloads mean sudden infra spend and new observability need
AI_WORKLOAD_KEYWORDS = [
    "gpu", "llm", "inference at scale", "model serving", "vector database",
    "training pipeline", "mlops", "ml platform", "ai infrastructure",
    "genai", "rag pipeline",
]

# International expansion drives multi-region infra
EXPANSION_KEYWORDS = [
    "multi-region", "global expansion", "us market", "eu region",
    "international expansion", "new geography", "apac expansion",
    "expanding to", "global rollout",
]

# ---------------------------------------------------------------------------
# INDUSTRY TIERS
# ---------------------------------------------------------------------------
INDUSTRY_TIERS = {
    # Tier 1, highest value per account
    "BFSI": 1, "Fintech": 1, "Insurtech": 1, "Manufacturing": 1,
    # Tier 2, highest volume
    "Software": 2, "Internet": 2, "SaaS": 2, "Devtools": 2, "AI": 2,
    "Ecommerce": 2, "Gaming": 2,
    # Tier 3
    "IT Services": 3, "Professional Services": 3, "Edtech": 3,
    # Outside stated priorities
    "Healthtech": 4, "Logistics": 4, "Agritech": 4, "D2C": 4,
    "Mobility": 4, "Proptech": 4, "Unclassified": 4,
}

TIER_MULTIPLIER = {1: 1.35, 2: 1.20, 3: 1.00, 4: 0.75}

# ---------------------------------------------------------------------------
# SCORING
# ---------------------------------------------------------------------------
SCORE_WEIGHTS = {
    # Budget triggers, your top-ranked signal group
    "funding_seed": 25,
    "funding_series_a": 40,
    "funding_series_b": 45,
    "funding_series_c": 40,
    "funding_other": 20,
    "ipo": 40,
    "cloud_migration": 35,
    "ai_workloads": 25,
    "expansion": 22,

    # Infra fit
    "cloud_confirmed": 25,
    "observability_stack": 28,
    "competitor_mention": 22,
    "infra_keyword": 4,          # per keyword, capped below

    # Engineering org
    "eng_team_depth": 18,        # meets MIN_ENGINEERING_ROLES
    "leadership_hire": 12,
    "new_reliability_role": 12,  # per role, capped below

    # Hard evidence from public code, worth more than a job ad mention
    "github_kubernetes": 30,
    "github_terraform": 25,
    "github_docker": 12,
    "github_infra_repo": 10,

    # Reliability pain, happening now
    "status_incidents": 26,
    "status_page_exists": 8,
    "blog_infra_topic": 18,

    # Trajectory beats snapshot
    "velocity_accelerating": 30,
    "velocity_growing": 15,
}

SCORE_CAPS = {
    "infra_keyword": 32,
    "new_reliability_role": 30,
}

# --- extra signal sources -------------------------------------------------
# GitHub is free. In GitHub Actions, secrets.GITHUB_TOKEN is provided
# automatically and raises the limit from 60 to 5000 requests an hour.
USE_GITHUB = True

# Status pages and engineering blogs. Free, needs a domain, which GitHub gives us.
USE_WEB_SIGNALS = True

# LLM briefs. The only paid part. Off unless ANTHROPIC_API_KEY is set.
USE_LLM_BRIEFS = True
LLM_BRIEF_LIMIT = 15          # cap accounts enriched per run, controls cost

MIN_SCORE_TO_REPORT = 60
MIN_SCORE_FOR_WATCHLIST = 35

# Cloud evidence is a hard ICP requirement for a confirmed account.
REQUIRE_CLOUD_FOR_QUALIFIED = True
REQUIRE_FUNDING_FOR_HIGH = True

# ---------------------------------------------------------------------------
# HEADCOUNT
# ---------------------------------------------------------------------------
HEADCOUNT_CEILING = 1000
USE_WIKIDATA = True

# How to handle a company whose headcount cannot be confirmed.
#
#   "strict"    keep only if the WHOLE estimated band sits under the ceiling.
#               Drops Series C and heavy hirers. Fewer accounts, none too big.
#   "balanced"  keep unless the band sits entirely above the ceiling.
#   "loose"     keep unless a confirmed figure exceeds the ceiling.
#
HEADCOUNT_STRICTNESS = "strict"

# Companies known to be over 1000 in India. Free data will not catch these
# reliably, so they are hard-blocked by name. Add any that slip through.
KNOWN_TOO_LARGE = [
    "postman", "zeta", "cred", "groww", "navi", "swiggy", "zomato", "meesho",
    "phonepe", "razorpay", "paytm", "byju", "unacademy", "dream11", "sharechat",
    "flipkart", "myntra", "nykaa", "lenskart", "delhivery", "zerodha", "policybazaar",
    "freshworks", "zoho", "innovaccer", "browserstack", "chargebee", "darwinbox",
    "icertis", "mindtickle", "whatfix", "cleartax", "urban company", "oyo",
    "ola", "uber", "amazon", "flipkart", "pharmeasy", "practo", "healthifyme",
    "zetwerk", "udaan", "cars24", "spinny", "licious", "rebel foods", "boat",
    "mamaearth", "ather", "zepto", "blinkit", "dunzo", "porter", "shiprocket",
    "moglix", "ninjacart", "dehaat", "capillary", "quantiphi", "tredence",
    "latentview", "fractal", "mu sigma", "gupshup", "exotel", "amagi",
    "uniphore", "yellow.ai", "sirionlabs", "zenoti", "clevertap", "moengage",
    "juspay", "perfios", "kreditbee", "slice", "m2p", "yubi", "keka",
]

MAX_OPEN_ROLES = 150
EXCLUDE_STAGES = ["series d", "series e", "series f", "series g", "pre-ipo"]

EXCLUDE_COMPANIES = [
    "signoz", "grafana", "datadog", "new relic", "dynatrace", "splunk",
    "elastic", "sumo logic", "honeycomb", "lightstep", "chronosphere",
    "middleware", "last9", "levitate",
]

OWN_PRODUCT_KEYWORDS = ["datadog", "dd agent", "datadoghq"]

# An account that already mentions Datadog is not a fresh account. Cap it so it
# never outranks a clean one, and never let it reach High.
EXISTING_CUSTOMER_PENALTY = 0.55
EXISTING_CUSTOMER_MAX_PRIORITY = "Medium"

# ---------------------------------------------------------------------------
# EMAIL
# ---------------------------------------------------------------------------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_TO = os.getenv("EMAIL_TO", "tanushree.dutta@datadoghq.com")
EMAIL_SUBJECT = "Account signals digest, {date}"

DB_PATH = os.getenv("DB_PATH", "signalbot.db")
REQUEST_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (compatible; AccountSignalBot/1.0)"

# Legacy aliases kept so older modules keep importing cleanly
SCALE_KEYWORDS = INFRA_COMPLEXITY
CLOUD_KEYWORDS = CLOUD_PROVIDERS
