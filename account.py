"""
Account record builder, driven by the ICP in config.py.

An account is scored in four blocks:

  1. Budget trigger   funding, IPO, migration, AI workloads, expansion
  2. Infra fit        cloud confirmed, monitoring stack, complexity keywords
  3. Engineering org  team depth, leadership, reliability hiring
  4. Industry tier    multiplier applied at the end

Two hard gates run before any of that: headcount under the ceiling, and
evidence of cloud. On-prem with no migration intent is outside the ICP.
"""

import re

import config
import headcount

W = config.SCORE_WEIGHTS
CAPS = config.SCORE_CAPS


def _matches(text, keywords):
    lowered = text.lower()
    return sorted({k for k in keywords if k in lowered})


# ---------------------------------------------------------------------------
# Industry classification, mapped to your tier list
# ---------------------------------------------------------------------------
INDUSTRY_SIGNALS = {
    "Fintech": ["payments", "upi", "neobank", "lending", "credit underwriting",
                "wealth management", "mutual fund", "trading platform", "kyc"],
    "BFSI": ["bank", "banking", "nbfc", "capital markets", "core banking",
             "treasury", "regulatory reporting", "rbi"],
    "Insurtech": ["insurance", "policy issuance", "claims processing", "actuarial"],
    "Manufacturing": ["manufacturing", "plant", "shop floor", "industrial iot",
                      "scada", "production line", "supply chain planning", "erp"],
    "SaaS": ["saas", "b2b software", "multi-tenant", "subscription billing",
             "customer onboarding", "crm", "product-led"],
    "Devtools": ["developer tools", "api platform", "sdk", "developer experience",
                 "open source", "ci/cd platform"],
    "AI": ["llm", "machine learning", "genai", "model serving", "computer vision",
           "nlp", "inference"],
    "Ecommerce": ["ecommerce", "e-commerce", "marketplace", "catalog", "checkout",
                  "storefront", "d2c"],
    "IT Services": ["client engagements", "staff augmentation", "consulting projects",
                    "system integration", "managed services"],
    "Edtech": ["learner", "curriculum", "course delivery", "student", "edtech"],
    "Healthtech": ["patient", "clinical", "diagnostics", "ehr", "telemedicine"],
    "Logistics": ["logistics", "fleet", "last mile", "warehouse", "shipment"],
    "Gaming": ["game", "gaming", "multiplayer", "matchmaking"],
}


def classify_industry(text, declared=""):
    if declared and declared in config.INDUSTRY_TIERS:
        return declared
    lowered = text.lower()
    best, best_hits = "", 0
    for label, words in INDUSTRY_SIGNALS.items():
        hits = sum(1 for w in words if w in lowered)
        if hits > best_hits:
            best, best_hits = label, hits
    return best if best_hits >= 2 else "Unclassified"


def is_excluded(name):
    lowered = (name or "").lower()
    return any(bad in lowered for bad in config.EXCLUDE_COMPANIES)


def _count_engineering_roles(jobs):
    return sum(
        1 for j in jobs
        if any(k in j["title"].lower() for k in config.ENGINEERING_ROLE_KEYWORDS)
    )


# ---------------------------------------------------------------------------
def build_account(company, jobs, new_jobs, previous_role_count=None,
                  gh=None, web=None, velocity=None):
    score = 0
    signals = []
    blockers = []
    has_board = bool(jobs)
    all_text = " ".join(f"{j['title']} {j['description']}" for j in jobs)
    lowered = all_text.lower()
    stage = (company.get("funding_stage") or "unknown").lower()
    news_text = f"{company.get('headline','')} {company.get('sector','')}".lower()

    # === BLOCK 1: budget triggers ==========================================
    stage_key = {
        "seed": "funding_seed", "pre-seed": "funding_seed",
        "series a": "funding_series_a", "series b": "funding_series_b",
        "series c": "funding_series_c",
    }.get(stage)

    funding_label = ""
    if stage_key:
        score += W[stage_key]
        funding_label = f"{stage.title()} {company.get('funding_amount','')}".strip()
        signals.append(f"Raised {funding_label}")
    elif company.get("funding_url"):
        score += W["funding_other"]
        funding_label = company.get("funding_amount", "Recent round")
        signals.append("Recent funding round")

    if re.search(r"\bipo\b|listing|listed on (nse|bse)", news_text):
        score += W["ipo"]
        signals.append("IPO or public listing event")

    migration = _matches(lowered, config.MIGRATION_KEYWORDS) + \
                _matches(news_text, config.MIGRATION_KEYWORDS)
    if migration:
        score += W["cloud_migration"]
        signals.append(f"Cloud migration underway ({migration[0]})")

    ai_work = _matches(lowered, config.AI_WORKLOAD_KEYWORDS)
    if ai_work:
        score += W["ai_workloads"]
        signals.append(f"Scaling AI workloads ({', '.join(ai_work[:2])})")

    expansion = _matches(lowered, config.EXPANSION_KEYWORDS) + \
                _matches(news_text, config.EXPANSION_KEYWORDS)
    if expansion:
        score += W["expansion"]
        signals.append(f"Geographic expansion ({expansion[0]})")

    # === BLOCK 2: infra fit ================================================
    clouds = _matches(lowered, config.CLOUD_PROVIDERS)
    onprem = _matches(lowered, config.ONPREM_KEYWORDS)

    cloud_native = bool(clouds)
    cloud_migrating = bool(migration)

    if cloud_native:
        score += W["cloud_confirmed"]
        primary = clouds[0].upper() if len(clouds[0]) <= 5 else clouds[0].title()
        signals.append(f"Production on cloud ({', '.join(clouds[:3])})")
    elif onprem and not cloud_migrating:
        blockers.append("On-prem with no migration signal, outside ICP")

    obs_stack = _matches(lowered, config.OBSERVABILITY_STACK)
    if obs_stack:
        score += W["observability_stack"]
        signals.append(f"Self-hosted monitoring ({', '.join(obs_stack[:3])})")

    own_product = [k for k in config.OWN_PRODUCT_KEYWORDS if k in lowered]
    rivals = _matches(lowered, config.COMPETITOR_KEYWORDS)
    if own_product:
        signals.append("Already running Datadog, check CRM first")
    if rivals:
        score += W["competitor_mention"]
        signals.append(f"Competitor in place ({', '.join(rivals[:2])}), displacement")

    infra = _matches(lowered, config.INFRA_COMPLEXITY)
    if infra:
        score += min(len(infra) * W["infra_keyword"], CAPS["infra_keyword"])
        signals.append(f"Infra complexity ({', '.join(infra[:4])})")

    # === BLOCK 3: engineering org ==========================================
    eng_roles = _count_engineering_roles(jobs)
    if eng_roles >= config.MIN_ENGINEERING_ROLES:
        score += W["eng_team_depth"]
        signals.append(f"{eng_roles} engineering roles open, real infra team")
    elif has_board and eng_roles == 0:
        blockers.append("No engineering hiring visible")

    leadership = [j for j in jobs
                  if any(k in j["title"].lower() for k in config.LEADERSHIP_ROLE_KEYWORDS)]
    if leadership:
        score += W["leadership_hire"]
        signals.append(f"Eng leadership hire ({leadership[0]['title']})")

    reliability = [j for j in jobs
                   if any(k in j["title"].lower() for k in config.RELIABILITY_ROLE_KEYWORDS)]
    new_reliability = [j for j in new_jobs
                       if any(k in j["title"].lower() for k in config.RELIABILITY_ROLE_KEYWORDS)]
    if new_reliability:
        score += min(len(new_reliability) * W["new_reliability_role"],
                     CAPS["new_reliability_role"])
        signals.append(f"Hiring {len(new_reliability)} SRE/DevOps role(s)")
    elif reliability:
        score += 8
        signals.append(f"{len(reliability)} SRE/DevOps role(s) open")

    # === BLOCK 3b: hard evidence from public code =========================
    gh = gh or {}
    gh_evidence = list(gh.get("evidence", []))
    if gh:
        repos_text = " ".join(gh.get("infra_repos", [])).lower()
        if "helm" in repos_text or "chart" in repos_text or "k8s" in repos_text \
                or "kubernetes" in repos_text or "kubernetes" in gh.get("topics", []):
            score += W["github_kubernetes"]
            cloud_native = True
        if "Terraform" in gh.get("infra_languages", []):
            score += W["github_terraform"]
            cloud_native = True
        if "Docker" in gh.get("infra_languages", []):
            score += W["github_docker"]
        if gh.get("infra_repos"):
            score += W["github_infra_repo"]
        for line in gh_evidence:
            signals.append(f"GitHub: {line}")

    # === BLOCK 3c: reliability pain, happening now ========================
    web = web or {}
    web_signal_lines = list(web.get("signals", []))
    status = web.get("status_page")
    if status:
        if status.get("recent_incidents", 0) > 0:
            score += W["status_incidents"]
        else:
            score += W["status_page_exists"]
    if web.get("blog"):
        score += W["blog_infra_topic"]
    for line in web_signal_lines:
        signals.append(line)

    # === BLOCK 3d: trajectory =============================================
    velocity_note = ""
    if velocity:
        velocity_note = velocity.get("note", "")
        if velocity["trend"] == "accelerating":
            score += W["velocity_accelerating"]
            signals.append(f"Hiring accelerating, {velocity_note}")
        elif velocity["trend"] == "growing":
            score += W["velocity_growing"]
            signals.append(f"Hiring growing, {velocity_note}")

    # === BLOCK 4: industry tier ============================================
    industry = classify_industry(all_text + " " + news_text, company.get("sector", ""))
    tier = config.INDUSTRY_TIERS.get(industry, 4)
    score = int(score * config.TIER_MULTIPLIER[tier])

    # === GATES =============================================================
    size = headcount.assess(company.get("name", ""), stage, len(jobs),
                            use_wikidata=config.USE_WIKIDATA)

    icp_fit = True
    if not size["in_band"]:
        icp_fit = False
        blockers.append(size["reason"])
    if (has_board and config.REQUIRE_CLOUD_FOR_QUALIFIED
            and not (cloud_native or cloud_migrating or gh_evidence)):
        icp_fit = False
        blockers.append("No AWS, Azure or GCP evidence found")

    # === PRIORITY ==========================================================
    has_budget_trigger = bool(stage_key or company.get("funding_url")
                              or migration or expansion or ai_work)
    if score >= 130 and (has_budget_trigger or not config.REQUIRE_FUNDING_FOR_HIGH):
        priority = "High"
    elif score >= 80:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "company": company.get("name", ""),
        "industry": industry,
        "tier": tier,
        "employees": size["estimate"],
        "employees_source": size["source"],
        "in_band": size["in_band"],
        "icp_fit": icp_fit,
        "size_reason": size["reason"],
        "funding_stage": stage.title() if stage != "unknown" else "",
        "funding_amount": company.get("funding_amount", ""),
        "funding_label": funding_label,
        "investors": company.get("investors", ""),
        "funding_date": company.get("published", ""),
        "cloud": ", ".join(clouds[:3]),
        "signals": signals,
        "blockers": blockers,
        "stack": ", ".join((obs_stack + infra)[:6]),
        "open_roles": len(jobs),
        "engineering_roles": eng_roles,
        "reliability_roles": len(reliability),
        "verified": has_board or bool(gh_evidence),
        "existing_customer": bool(own_product),
        "github_org": gh.get("org", ""),
        "github_evidence": gh_evidence,
        "domain": gh.get("domain", ""),
        "india_confirmed": gh.get("india_confirmed", False),
        "web_signals": web_signal_lines,
        "status_page": (status or {}).get("url", ""),
        "velocity_note": velocity_note,
        "score": score,
        "priority": priority,
        "source_url": company.get("funding_url", ""),
        "headline": company.get("headline", ""),
    }
